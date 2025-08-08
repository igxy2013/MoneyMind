import pymysql
from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text('DESCRIBE receivable'))
            print('Current receivable table structure:')
            for row in result:
                print(row)
    except Exception as e:
        print(f'Error: {e}')
        print('Table might not exist or missing columns, creating/updating tables...')
        db.create_all()
        print('Tables created/updated successfully')
        
        # Check again after creation
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text('DESCRIBE receivable'))
                print('\nUpdated receivable table structure:')
                for row in result:
                    print(row)
        except Exception as e2:
            print(f'Error checking updated structure: {e2}')