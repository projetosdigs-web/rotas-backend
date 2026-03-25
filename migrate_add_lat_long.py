import sqlite3

DB_NAME = "rotas.db"


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1]
               for row in cursor.fetchall()]  # índice 1 = nome da coluna
    return column_name in columns


def main():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    print(f"Conectado ao banco: {DB_NAME}")

    # --- Verificar e criar colunas em cities ---
    print("\nVerificando tabela 'cities'...")

    if not column_exists(cur, "cities", "latitude"):
        print("➕ Adicionando coluna 'latitude' em 'cities'...")
        cur.execute("ALTER TABLE cities ADD COLUMN latitude REAL;")
    else:
        print("✔ Coluna 'latitude' já existe em 'cities'.")

    if not column_exists(cur, "cities", "longitude"):
        print("➕ Adicionando coluna 'longitude' em 'cities'...")
        cur.execute("ALTER TABLE cities ADD COLUMN longitude REAL;")
    else:
        print("✔ Coluna 'longitude' já existe em 'cities'.")

    conn.commit()
    conn.close()
    print("\nMigração concluída com sucesso! ✅")


if __name__ == "__main__":
    main()
