# ask_db.py
from app.text_to_sql import TextToSQLAgent


def main():
    agent = TextToSQLAgent()
    print("=" * 60)
    print(" ConCallSense Text-to-SQL Engine (Type 'exit' to quit)")
    print("=" * 60)

    # Pre-tested sample queries
    print("Sample queries you can try:")
    print(" • What guidance targets did TCS provide?")
    print(" • List all commitments where target is an EBITDA margin.")
    print(" • Show companies with sentiment score above 0.5.")
    print("-" * 60)

    while True:
        try:
            question = input("\nAsk a question: ").strip()
            if not question:
                continue
            if question.lower() in ("exit", "quit"):
                break

            print("[*] Generating SQL and querying database...")
            result = agent.query(question)

            if "error" in result:
                print(f"[!] Error: {result['error']}")
                if "generated_sql" in result:
                    print(f"[SQL]: {result['generated_sql']}")
            else:
                print(f"[SQL]: {result['generated_sql']}\n")
                if not result["data"]:
                    print("No records matched your query.")
                else:
                    for i, row in enumerate(result["data"], 1):
                        print(f"Row {i}: {row}")

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()