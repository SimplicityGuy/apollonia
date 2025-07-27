"""Unit tests for the populator service."""

import asyncio
import logging
import signal
from unittest.mock import AsyncMock, patch

import orjson
import pytest
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection
from neo4j import AsyncDriver


class TestPopulator:
    """Test cases for the Populator class."""

    @pytest.fixture
    def mock_amqp_connection(self):
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
    def mock_neo4j_driver(self):
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
    def mock_message(self):
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
    async def test_populator_initialization(self):
        """Test that Populator can be initialized."""
        from populator.populator import Populator

        populator = Populator()
        assert populator.amqp_connection is None
        assert populator.neo4j_driver is None
        assert populator._running is True

    @pytest.mark.asyncio
    async def test_populator_context_manager_enter(self):
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

            mock_connect.return_value = amqp_connection
            mock_graph_db.driver.return_value = neo4j_driver
            neo4j_driver.session.return_value.__aenter__.return_value = neo4j_session
            neo4j_driver.session.return_value.__aexit__.return_value = None

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
    async def test_populator_context_manager_exit(self):
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

    def test_stop(self):
        """Test stop method sets _running to False."""
        from populator.populator import Populator

        populator = Populator()
        assert populator._running is True
        populator.stop()
        assert populator._running is False

    @pytest.mark.asyncio
    async def test_process_message_success(self, mock_neo4j_driver, mock_message):
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
        assert file_query_call[1]["file_path"] == "/test/file.txt"
        assert file_query_call[1]["sha256_hash"] == "abc123"
        assert file_query_call[1]["xxh128_hash"] == "def456"
        assert file_query_call[1]["size"] == 1024

        # Check neighbor relationships were created
        assert session.run.call_count == 3  # 1 for file + 2 for neighbors
        neighbor_calls = session.run.call_args_list[1:]
        for call in neighbor_calls:
            assert "MERGE (f1)-[:NEIGHBOR]->(f2)" in call[0][0]

    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, mock_neo4j_driver, mock_message):
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
    async def test_import_to_neo4j_no_driver(self, mock_message):
        """Test _import_to_neo4j returns early when no driver."""
        from populator.populator import Populator

        populator = Populator()
        populator.neo4j_driver = None

        # Should not raise exception
        data = orjson.loads(mock_message.body)
        await populator._import_to_neo4j(data)

    @pytest.mark.asyncio
    async def test_import_to_neo4j_with_minimal_data(self, mock_neo4j_driver):
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
        assert file_query_call[1]["file_path"] == "/test/minimal.txt"
        assert file_query_call[1]["sha256_hash"] == ""
        assert file_query_call[1]["xxh128_hash"] == ""
        assert file_query_call[1]["size"] == 0

    @pytest.mark.asyncio
    async def test_consume_setup_and_iteration(self, mock_amqp_connection):
        """Test consume sets up queue and processes messages."""
        from populator.populator import AMQP_EXCHANGE, AMQP_QUEUE, AMQP_ROUTING_KEY, Populator

        connection, channel, exchange, queue = mock_amqp_connection

        # Set up mock messages
        mock_msg1 = AsyncMock()
        mock_msg2 = AsyncMock()
        messages = [mock_msg1, mock_msg2]

        # Create async iterator for queue
        async def message_iterator():
            for msg in messages:
                if not populator._running:
                    return
                yield msg

        queue.iterator.return_value.__aenter__.return_value.__aiter__ = message_iterator

        # Create populator
        populator = Populator()
        populator.amqp_connection = connection
        populator.process_message = AsyncMock()

        # Stop after processing messages
        async def stop_after_messages():
            await asyncio.sleep(0.1)
            populator.stop()

        task = asyncio.create_task(stop_after_messages())
        await populator.consume()
        await task

        # Verify setup
        connection.channel.assert_called_once()
        channel.declare_exchange.assert_called_once_with(
            AMQP_EXCHANGE, type="fanout", durable=True, auto_delete=False
        )
        channel.declare_queue.assert_called_once_with(AMQP_QUEUE, durable=True, auto_delete=False)
        queue.bind.assert_called_once_with(exchange, routing_key=AMQP_ROUTING_KEY)

        # Verify messages were processed
        assert populator.process_message.call_count == 2
        populator.process_message.assert_any_call(mock_msg1)
        populator.process_message.assert_any_call(mock_msg2)

    @pytest.mark.asyncio
    async def test_consume_no_connection(self):
        """Test consume returns early when no connection."""
        from populator.populator import Populator

        populator = Populator()
        populator.amqp_connection = None

        # Should not raise exception
        await populator.consume()

    def test_setup_logging(self):
        """Test logging setup."""
        with patch("populator.populator.logging.basicConfig") as mock_config:
            from populator.populator import setup_logging

            setup_logging()

            mock_config.assert_called_once()
            args = mock_config.call_args
            assert args.kwargs["level"] == logging.INFO
            assert "%(asctime)s" in args.kwargs["format"]
            assert len(args.kwargs["handlers"]) == 1

    def test_print_banner(self, capsys):
        """Test banner printing."""
        from populator.populator import print_banner

        print_banner()

        captured = capsys.readouterr()
        assert "apollonia" in captured.out.lower()
        assert "populator" in captured.out.lower()

    @pytest.mark.asyncio
    async def test_async_main_signal_handling(self):
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
    async def test_async_main_keyboard_interrupt(self):
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
    async def test_async_main_fatal_error(self):
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

    def test_main_missing_amqp_connection(self):
        """Test main exits when AMQP connection string is missing."""
        with (
            patch("populator.populator.setup_logging"),
            patch("populator.populator.print_banner"),
            patch("populator.populator.AMQP_CONNECTION", ""),
            patch("populator.populator.sys.exit") as mock_exit,
        ):
            from populator.populator import main

            main()

            mock_exit.assert_called_once_with(1)

    def test_main_default_neo4j_password_warning(self, caplog):
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

    def test_main_successful_run(self):
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
