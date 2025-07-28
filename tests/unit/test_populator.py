"""Unit tests for the populator service."""

import asyncio
import logging
import signal
from typing import Any
from unittest.mock import AsyncMock, patch

import orjson
import pytest
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection
from neo4j import AsyncDriver


class TestPopulator:
    """Test cases for the Populator class."""

    @pytest.fixture
    def mock_amqp_connection(self) -> tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
        """Create a mock AMQP connection."""
        connection = AsyncMock(spec=AbstractRobustConnection)
        channel = AsyncMock()
        exchange = AsyncMock()
        queue = AsyncMock()

        # Set up the mock chain
        connection.channel.return_value = channel
        channel.declare_exchange.return_value = exchange
        channel.declare_queue.return_value = queue
        queue.bind = AsyncMock()

        return connection, channel, exchange, queue

    @pytest.fixture
    def mock_neo4j_driver(self) -> tuple[AsyncMock, AsyncMock]:
        """Create a mock Neo4j driver."""
        driver = AsyncMock(spec=AsyncDriver)
        session = AsyncMock()
        result = AsyncMock()

        # Set up the mock chain
        driver.session.return_value.__aenter__.return_value = session
        driver.session.return_value.__aexit__.return_value = None
        session.run.return_value = result
        result.single.return_value = {"f": {"path": "/test/file.txt"}}

        return driver, session

    @pytest.fixture
    def mock_message(self) -> AsyncMock:
        """Create a mock AMQP message."""
        message = AsyncMock(spec=AbstractIncomingMessage)
        message.body = orjson.dumps(
            {
                "file_path": "/test/file.txt",
                "sha256_hash": "abc123",
                "xxh128_hash": "def456",
                "size": 1024,
                "modified_time": "2024-01-01T00:00:00",
                "accessed_time": "2024-01-01T00:00:00",
                "changed_time": "2024-01-01T00:00:00",
                "timestamp": "2024-01-01T00:00:00",
                "event_type": "IN_CREATE",
                "neighbors": ["/test/file2.txt", "/test/file3.txt"],
            }
        )

        # Set up process context manager
        process_mock = AsyncMock()
        process_mock.__aenter__ = AsyncMock(return_value=None)
        process_mock.__aexit__ = AsyncMock(return_value=None)
        message.process.return_value = process_mock

        return message

    @pytest.mark.asyncio
    async def test_populator_initialization(self) -> None:
        """Test that Populator can be initialized."""
        from populator.populator import Populator

        populator = Populator()
        assert populator.amqp_connection is None
        assert populator.neo4j_driver is None
        assert populator._running is True

    @pytest.mark.asyncio
    async def test_populator_context_manager_enter(self) -> None:
        """Test __aenter__ sets up connections properly."""
        with (
            patch("populator.populator.connect_robust") as mock_connect,
            patch("populator.populator.AsyncGraphDatabase") as mock_graph_db,
        ):
            from populator.populator import (
                AMQP_CONNECTION,
                NEO4J_PASSWORD,
                NEO4J_URI,
                NEO4J_USER,
                Populator,
            )

            # Set up mocks
            amqp_connection = AsyncMock()
            neo4j_driver = AsyncMock()
            neo4j_session = AsyncMock()
            neo4j_result = AsyncMock()

            # Create proper coroutine for connect_robust
            async def async_connect(*args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
                return amqp_connection

            mock_connect.side_effect = async_connect
            mock_graph_db.driver.return_value = neo4j_driver
            # Create a proper async context manager for neo4j session
            session_context = AsyncMock()

            # Make __aenter__ return a coroutine that returns neo4j_session
            async def aenter_coro(*args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
                return neo4j_session

            async def aexit_coro(*args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
                return None

            session_context.__aenter__ = aenter_coro
            session_context.__aexit__ = aexit_coro
            neo4j_driver.session.return_value = session_context
            neo4j_session.run = AsyncMock(return_value=neo4j_result)

            # Create populator
            populator = Populator()
            result = await populator.__aenter__()

            # Verify
            assert result is populator
            mock_connect.assert_called_once_with(AMQP_CONNECTION)
            mock_graph_db.driver.assert_called_once_with(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            assert populator.amqp_connection is amqp_connection
            assert populator.neo4j_driver is neo4j_driver

            # Verify Neo4j connection was tested
            neo4j_session.run.assert_called_once_with("RETURN 1")

    @pytest.mark.asyncio
    async def test_populator_context_manager_exit(self) -> None:
        """Test __aexit__ closes connections properly."""
        from populator.populator import Populator

        # Create populator with mock connections
        populator = Populator()
        populator.amqp_connection = AsyncMock()
        populator.neo4j_driver = AsyncMock()

        # Test exit
        await populator.__aexit__(None, None, None)

        # Verify connections were closed
        populator.amqp_connection.close.assert_called_once()
        populator.neo4j_driver.close.assert_called_once()

    def test_stop(self) -> None:
        """Test stop method sets _running to False."""
        from populator.populator import Populator

        populator = Populator()
        assert populator._running is True
        populator.stop()
        assert populator._running is False

    @pytest.mark.asyncio
    async def test_process_message_success(
        self, mock_neo4j_driver: tuple[AsyncMock, AsyncMock], mock_message: AsyncMock
    ) -> None:
        """Test successful message processing."""
        from populator.populator import Populator

        driver, session = mock_neo4j_driver

        # Create populator
        populator = Populator()
        populator.neo4j_driver = driver

        # Process message
        await populator.process_message(mock_message)

        # Verify message was processed
        mock_message.process.assert_called_once()

        # Verify Neo4j operations
        assert session.run.call_count >= 1

        # Check the file node creation query
        file_query_call = session.run.call_args_list[0]
        assert "MERGE (f:File {path: $file_path})" in file_query_call[0][0]
        # Check positional arguments (query) and keyword arguments (params)
        params = file_query_call[0][1] if len(file_query_call[0]) > 1 else file_query_call[1]
        assert params["file_path"] == "/test/file.txt"
        assert params["sha256_hash"] == "abc123"
        assert params["xxh128_hash"] == "def456"
        assert params["size"] == 1024

        # Check neighbor relationships were created
        assert session.run.call_count == 3  # 1 for file + 2 for neighbors
        neighbor_calls = session.run.call_args_list[1:]
        for call in neighbor_calls:
            assert "MERGE (f1)-[:NEIGHBOR]->(f2)" in call[0][0]

    @pytest.mark.asyncio
    async def test_process_message_error_handling(
        self, mock_neo4j_driver: tuple[AsyncMock, AsyncMock], mock_message: AsyncMock
    ) -> None:
        """Test message processing handles errors gracefully."""
        from populator.populator import Populator

        driver, session = mock_neo4j_driver

        # Make Neo4j operation fail
        session.run.side_effect = Exception("Database error")

        # Create populator
        populator = Populator()
        populator.neo4j_driver = driver

        # Process message - should not raise exception
        await populator.process_message(mock_message)

        # Verify message was processed (context manager entered)
        mock_message.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_to_neo4j_no_driver(self, mock_message: AsyncMock) -> None:
        """Test _import_to_neo4j returns early when no driver."""
        from populator.populator import Populator

        populator = Populator()
        populator.neo4j_driver = None

        # Should not raise exception
        data = orjson.loads(mock_message.body)
        await populator._import_to_neo4j(data)

    @pytest.mark.asyncio
    async def test_import_to_neo4j_with_minimal_data(
        self, mock_neo4j_driver: tuple[AsyncMock, AsyncMock]
    ) -> None:
        """Test _import_to_neo4j handles minimal data correctly."""
        from populator.populator import Populator

        driver, session = mock_neo4j_driver

        # Minimal data
        data = {"file_path": "/test/minimal.txt", "event_type": "IN_CREATE"}

        populator = Populator()
        populator.neo4j_driver = driver

        await populator._import_to_neo4j(data)

        # Verify file node was created with defaults
        file_query_call = session.run.call_args_list[0]
        # Check positional arguments (query) and keyword arguments (params)
        params = file_query_call[0][1] if len(file_query_call[0]) > 1 else file_query_call[1]
        assert params["file_path"] == "/test/minimal.txt"
        assert params["sha256_hash"] == ""
        assert params["xxh128_hash"] == ""
        assert params["size"] == 0

    @pytest.mark.asyncio
    async def test_consume_setup_and_iteration(
        self, mock_amqp_connection: tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock]
    ) -> None:
        """Test consume sets up queue and processes messages."""
        from populator.populator import AMQP_EXCHANGE, AMQP_QUEUE, AMQP_ROUTING_KEY, Populator

        connection, channel, exchange, queue = mock_amqp_connection

        # Set up mock messages
        mock_msg1 = AsyncMock()
        mock_msg2 = AsyncMock()
        messages = [mock_msg1, mock_msg2]

        # Create async iterator for queue
        async def message_iterator() -> Any:
            for msg in messages:
                if not populator._running:
                    return
                yield msg

        # Create a proper async context manager for queue.iterator()
        iterator_context = AsyncMock()
        iterator_context.__aenter__.return_value = AsyncMock()
        iterator_context.__aenter__.return_value.__aiter__ = message_iterator
        iterator_context.__aexit__.return_value = None
        queue.iterator.return_value = iterator_context

        # Create populator
        populator = Populator()
        populator.amqp_connection = connection
        # Create a proper async mock for process_message
        mock_process = AsyncMock()
        # Use setattr to avoid mypy method assignment error
        setattr(populator, "process_message", mock_process)  # noqa: B010

        # Stop after processing messages
        async def stop_after_messages() -> None:
            await asyncio.sleep(0.1)
            populator.stop()

        # Run consume with a timeout
        task = asyncio.create_task(stop_after_messages())
        # Use contextlib.suppress for cleaner exception handling
        from contextlib import suppress

        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(populator.consume(), timeout=1.0)
        await task

        # Verify setup
        connection.channel.assert_called_once()
        channel.declare_exchange.assert_called_once_with(
            AMQP_EXCHANGE, type="fanout", durable=True, auto_delete=False
        )
        channel.declare_queue.assert_called_once_with(AMQP_QUEUE, durable=True, auto_delete=False)
        queue.bind.assert_called_once_with(exchange, routing_key=AMQP_ROUTING_KEY)

        # Verify messages were processed
        mock_process = getattr(populator, "process_message")  # noqa: B009
        assert mock_process.call_count == 2
        mock_process.assert_any_call(mock_msg1)
        mock_process.assert_any_call(mock_msg2)

    @pytest.mark.asyncio
    async def test_consume_no_connection(self) -> None:
        """Test consume returns early when no connection."""
        from populator.populator import Populator

        populator = Populator()
        populator.amqp_connection = None

        # Should not raise exception
        await populator.consume()

    def test_setup_logging(self) -> None:
        """Test logging setup."""
        with patch("populator.populator.logging.basicConfig") as mock_config:
            from populator.populator import setup_logging

            setup_logging()

            mock_config.assert_called_once()
            args = mock_config.call_args
            assert args.kwargs["level"] == logging.INFO
            assert "%(asctime)s" in args.kwargs["format"]
            assert len(args.kwargs["handlers"]) == 1

    def test_print_banner(self, capsys: Any) -> None:
        """Test banner printing."""
        from populator.populator import print_banner

        print_banner()

        captured = capsys.readouterr()
        # The banner is ASCII art, just verify it prints something
        assert len(captured.out) > 0
        assert "___" in captured.out  # Part of the ASCII art

    @pytest.mark.asyncio
    async def test_async_main_signal_handling(self) -> None:
        """Test async_main sets up signal handlers correctly."""
        with (
            patch("populator.populator.signal.signal") as mock_signal,
            patch("populator.populator.Populator") as mock_populator_class,
        ):
            from populator.populator import async_main

            # Set up mock
            mock_populator = AsyncMock()
            mock_populator_class.return_value.__aenter__.return_value = mock_populator
            mock_populator_class.return_value.__aexit__.return_value = None

            # Run
            await async_main()

            # Verify signal handlers were registered
            assert mock_signal.call_count >= 2
            signal_calls = mock_signal.call_args_list
            signals_registered = [call[0][0] for call in signal_calls]
            assert signal.SIGINT in signals_registered
            assert signal.SIGTERM in signals_registered

    @pytest.mark.asyncio
    async def test_async_main_keyboard_interrupt(self) -> None:
        """Test async_main handles KeyboardInterrupt gracefully."""
        with patch("populator.populator.Populator") as mock_populator_class:
            from populator.populator import async_main

            # Make consume raise KeyboardInterrupt
            mock_populator = AsyncMock()
            mock_populator.consume.side_effect = KeyboardInterrupt()
            mock_populator_class.return_value.__aenter__.return_value = mock_populator
            mock_populator_class.return_value.__aexit__.return_value = None

            # Should not raise exception
            await async_main()

    @pytest.mark.asyncio
    async def test_async_main_fatal_error(self) -> None:
        """Test async_main handles fatal errors."""
        with (
            patch("populator.populator.Populator") as mock_populator_class,
            patch("populator.populator.sys.exit") as mock_exit,
        ):
            from populator.populator import async_main

            # Make consume raise exception
            mock_populator = AsyncMock()
            mock_populator.consume.side_effect = Exception("Fatal error")
            mock_populator_class.return_value.__aenter__.return_value = mock_populator
            mock_populator_class.return_value.__aexit__.return_value = None

            # Run
            await async_main()

            # Verify exit was called
            mock_exit.assert_called_once_with(1)

    @pytest.mark.timeout(2)  # 2 second timeout
    def test_main_missing_amqp_connection(self) -> None:
        """Test main exits when AMQP connection string is missing."""
        # Need to patch before import to ensure the module-level variables are set correctly
        import sys as sys_module

        # Remove the module if it's already imported
        if "populator.populator" in sys_module.modules:
            del sys_module.modules["populator.populator"]

        with (
            patch.dict("os.environ", {"AMQP_CONNECTION_STRING": ""}),
            patch("sys.exit") as mock_exit,
        ):
            # Now import with the patched environment
            from populator import populator

            # Call main
            populator.main()

            mock_exit.assert_called_once_with(1)

    def test_main_default_neo4j_password_warning(self, caplog: Any) -> None:
        """Test main warns about default Neo4j password."""
        with (
            patch("populator.populator.setup_logging"),
            patch("populator.populator.print_banner"),
            patch("populator.populator.AMQP_CONNECTION", "amqp://test:test@localhost:5672/"),
            patch("populator.populator.NEO4J_PASSWORD", "password"),
            patch("populator.populator.asyncio.run") as mock_run,
        ):
            from populator.populator import main

            with caplog.at_level(logging.WARNING):
                main()

            # Verify warning was logged
            assert "Using default Neo4j password" in caplog.text
            mock_run.assert_called_once()

    def test_main_successful_run(self) -> None:
        """Test main runs successfully with proper configuration."""
        with (
            patch("populator.populator.setup_logging"),
            patch("populator.populator.print_banner"),
            patch("populator.populator.AMQP_CONNECTION", "amqp://test:test@localhost:5672/"),
            patch("populator.populator.NEO4J_PASSWORD", "secure_password"),
            patch("populator.populator.asyncio.run") as mock_run,
        ):
            from populator.populator import main

            main()

            mock_run.assert_called_once()
