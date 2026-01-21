from utils.parser import parse_args

from utils.logger import setup_logger


def main():
    logger = setup_logger()
    args = parse_args()
    logger.info("Starting CorteXForge...")
    logger.info(f"Args={args}")

    if args.role == "rx":
        from radio.rx import main as rx_main

        rx_main(args)
    elif args.role == "tx":
        from radio.tx import main as tx_main

        tx_main(args)
    else:
        raise ValueError(f"Unknown role: {args.role}")


if __name__ == "__main__":
    main()
