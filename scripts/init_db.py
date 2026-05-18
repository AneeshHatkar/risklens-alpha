from backend.app.database import init_db


def main():
    init_db()
    print("RiskLens Alpha database initialized.")


if __name__ == "__main__":
    main()
