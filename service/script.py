from database.base import get_db
from database_operations import create_tables, store_taco_dataset

(get_db())


def main():
    # Create tables
    create_tables()
    db = next(get_db())
    try:
        for i in range(3, 6):
            file_name = f'D:\\Downloads\\data3_5\\data-0000{i}-of-00009.arrow'
            store_taco_dataset(db, file_name)
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    main()