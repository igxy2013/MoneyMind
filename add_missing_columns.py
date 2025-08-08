from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        with db.engine.connect() as conn:
            # Add missing columns to receivable table
            columns_to_add = [
                "ALTER TABLE receivable ADD COLUMN receivable_number VARCHAR(50) UNIQUE",
                "ALTER TABLE receivable ADD COLUMN received_amount FLOAT DEFAULT 0.0",
                "ALTER TABLE receivable ADD COLUMN invoice_date DATE",
                "ALTER TABLE receivable ADD COLUMN payment_terms INT DEFAULT 30",
                "ALTER TABLE receivable ADD COLUMN contact_person VARCHAR(100)",
                "ALTER TABLE receivable ADD COLUMN contact_phone VARCHAR(20)",
                "ALTER TABLE receivable ADD COLUMN contact_address TEXT"
            ]
            
            for sql in columns_to_add:
                try:
                    conn.execute(text(sql))
                    print(f"Successfully added column: {sql.split('ADD COLUMN')[1].split()[0]}")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print(f"Column already exists: {sql.split('ADD COLUMN')[1].split()[0]}")
                    else:
                        print(f"Error adding column: {e}")
            
            conn.commit()
            print("\nAll columns processed successfully!")
            
            # Verify the updated structure
            result = conn.execute(text('DESCRIBE receivable'))
            print('\nUpdated receivable table structure:')
            for row in result:
                print(row)
                
    except Exception as e:
        print(f'Error: {e}')