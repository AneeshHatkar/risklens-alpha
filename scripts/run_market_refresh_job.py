from backend.app.database import init_db
from backend.app.services.job_manager import run_market_refresh_job


def main():
    init_db()
    result = run_market_refresh_job()

    print("\nRiskLens Alpha Market Refresh Job")
    print("=" * 48)
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print("Details:")
    for key, value in result.get("details", {}).items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
