import time
import schedule

from main import run_pipeline


def main() -> None:
    schedule.every().day.at("03:00").do(run_pipeline)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
