from backend.app.database import init_db, SessionLocal
from backend.app.services.alert_engine import check_alerts_for_portfolios
from backend.app.services.alert_repository import alert_to_dict, list_alerts


def main():
    init_db()

    db = SessionLocal()
    try:
        result = check_alerts_for_portfolios(db)
        alerts = list_alerts(db, limit=10)

        print("\nRiskLens Alpha Alert Check")
        print("=" * 48)
        print(f"Portfolio count: {result['portfolio_count']}")
        print(f"Created alerts: {result['created_alert_count']}")

        print("\nRecent Alerts:")
        for alert in alerts:
            data = alert_to_dict(alert)
            print(f"- [{data['severity'].upper()}] {data['title']}: {data['message']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
