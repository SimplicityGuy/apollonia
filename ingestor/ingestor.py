from asyncio import get_event_loop
from os import getenv

from asyncinotify import Inotify, Mask
from orjson import OPT_INDENT_2, OPT_SORT_KEYS, dumps
from pika import BlockingConnection, DeliveryMode, URLParameters
from pika.spec import BasicProperties
from prospector import Prospector

AMQP_CONNECTION = getenv("AMQP_CONNECTION")  # format: amqp://user:password@server:port
AMQP_EXCHANGE = "apollonia-ingestor"
DATA_DIRECTORY = "/data"
ROUTING_KEY = "populator"


class Ingestor:
    def __init__(self):
        self.amqp_connection = None
        self.amqp_channel = None
        self.amqp_properties = BasicProperties(
            content_encoding="application/json", delivery_mode=DeliveryMode.Persistent
        )

    def __enter__(self):
        self.amqp_connection = BlockingConnection(URLParameters(AMQP_CONNECTION))
        self.amqp_channel = self.amqp_connection.channel()

        # Create the exchange to send the messages to.
        self.amqp_channel.exchange_declare(
            auto_delete=True, durable=True, exchange=AMQP_EXCHANGE, exchange_type="fanout"
        )

        # The exchange defined in `AMQP_EXCHANGE` fans out to a single queue.
        apollonia_queue_name = f"apollonia-{ROUTING_KEY}"

        self.amqp_channel.queue_declare(auto_delete=True, durable=True, queue=apollonia_queue_name)
        self.amqp_channel.queue_bind(
            exchange=AMQP_EXCHANGE, queue=apollonia_queue_name, routing_key=f"{ROUTING_KEY}"
        )

        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.amqp_connection.close()

    async def ingest(self):
        print(f" -=: Igesting from {DATA_DIRECTORY}. :=- ")
        with Inotify() as inotify:
            inotify.add_watch(DATA_DIRECTORY, Mask.CLOSE_WRITE)

            async for event in inotify:
                data = Prospector(event.path).prospect()
                self.amqp_channel.basic_publish(
                    body=dumps(data, option=OPT_SORT_KEYS | OPT_INDENT_2),
                    exchange=AMQP_EXCHANGE,
                    properties=self.amqp_properties,
                    routing_key=f"{ROUTING_KEY}",
                )


def main():
    print("                 ____          _         ")
    print(" ___ ____  ___  / / /__  ___  (_)__ _    ")
    print("/ _ `/ _ \/ _ \/ / / _ \/ _ \/ / _ `/    ")
    print("\_,_/ .__/\___/_/_/\___/_//_/_/\_,_/     ")
    print("   /_/(_)__  ___ ____ ___ / /____  ____  ")
    print("     / / _ \/ _ `/ -_|_-</ __/ _ \/ __/  ")
    print("    /_/_//_/\_, /\__/___/\__/\___/_/     ")
    print("           /___/                         ")
    print()
    loop = get_event_loop()
    try:
        with Ingestor() as ingestor:
            loop.run_until_complete(ingestor.ingest())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    main()
