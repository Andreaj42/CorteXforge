from cortexforge.cli.forge import parse_args
from cortexforge.utils.logger import setup_logger

logger = setup_logger()


def main() -> None:
    args = parse_args()
    logger.info("Starting CorteXForge...")
    logger.info(f"Args={args}")

    if args.role == "rx":
        from cortexforge.forge.radio.rx import main as rx_main

        rx_main(args)
    elif args.role == "tx":
        from cortexforge.forge.radio.tx import main as tx_main

        tx_main(args)
    else:
        raise ValueError(f"Unknown role: {args.role}")


if __name__ == "__main__":
    main()
