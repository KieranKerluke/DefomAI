-- Fix for the missing account_user check warning
-- This creates the account_user table if it doesn't exist already
DO $$
BEGIN
    -- Check if the account_user table exists in the basejump schema
    IF NOT EXISTS (
        SELECT FROM pg_tables 
        WHERE schemaname = 'basejump' 
        AND tablename = 'account_user'
    ) THEN
        -- Create the account_user table
        CREATE TABLE basejump.account_user (
            user_id      uuid REFERENCES auth.users ON DELETE CASCADE NOT NULL,
            account_id   uuid REFERENCES basejump.accounts ON DELETE CASCADE NOT NULL,
            account_role basejump.account_role NOT NULL,
            CONSTRAINT account_user_pkey PRIMARY KEY (user_id, account_id)
        );

        -- Grant permissions
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE basejump.account_user TO authenticated, service_role;

        -- Enable RLS
        ALTER TABLE basejump.account_user ENABLE ROW LEVEL SECURITY;
    END IF;
END
$$;

-- Fix for the missing customer_id column in billing_customers table
DO $$
BEGIN
    -- Check if the customer_id column exists in the billing_customers table
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_schema = 'basejump' 
        AND table_name = 'billing_customers' 
        AND column_name = 'customer_id'
    ) THEN
        -- Add the customer_id column
        ALTER TABLE basejump.billing_customers 
        ADD COLUMN customer_id text;
        
        -- For existing records, set customer_id equal to id
        UPDATE basejump.billing_customers 
        SET customer_id = id 
        WHERE customer_id IS NULL;
    END IF;
END
$$;
