-- Check which column exists in ai_activation_codes and handle accordingly
DO $$
DECLARE
    has_code BOOLEAN;
    has_code_value BOOLEAN;
BEGIN
    -- Check if 'code' column exists
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_activation_codes' 
        AND column_name = 'code'
    ) INTO has_code;
    
    -- Check if 'code_value' column exists
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_activation_codes' 
        AND column_name = 'code_value'
    ) INTO has_code_value;
    
    -- If 'code' exists but 'code_value' doesn't, rename 'code' to 'code_value'
    IF has_code AND NOT has_code_value THEN
        ALTER TABLE public.ai_activation_codes 
        RENAME COLUMN code TO code_value;
        RAISE NOTICE 'Renamed column code to code_value in ai_activation_codes table';
    -- If neither column exists, add 'code_value'
    ELSIF NOT has_code AND NOT has_code_value THEN
        ALTER TABLE public.ai_activation_codes 
        ADD COLUMN code_value TEXT;
        RAISE NOTICE 'Added column code_value to ai_activation_codes table';
    -- If both columns exist, keep 'code_value' and drop 'code'
    ELSIF has_code AND has_code_value THEN
        ALTER TABLE public.ai_activation_codes 
        DROP COLUMN code;
        RAISE NOTICE 'Dropped duplicate column code from ai_activation_codes table';
    ELSE
        RAISE NOTICE 'Column code_value already exists in ai_activation_codes table';
    END IF;
    
    -- Do the same for ai_access_status table
    -- Check if 'code' column exists
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_access_status' 
        AND column_name = 'code'
    ) INTO has_code;
    
    -- Check if 'code_value' column exists
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_access_status' 
        AND column_name = 'code_value'
    ) INTO has_code_value;
    
    -- If 'code' exists but 'code_value' doesn't, rename 'code' to 'code_value'
    IF has_code AND NOT has_code_value THEN
        ALTER TABLE public.ai_access_status 
        RENAME COLUMN code TO code_value;
        RAISE NOTICE 'Renamed column code to code_value in ai_access_status table';
    -- If neither column exists, add 'code_value'
    ELSIF NOT has_code AND NOT has_code_value THEN
        ALTER TABLE public.ai_access_status 
        ADD COLUMN code_value TEXT;
        RAISE NOTICE 'Added column code_value to ai_access_status table';
    -- If both columns exist, keep 'code_value' and drop 'code'
    ELSIF has_code AND has_code_value THEN
        ALTER TABLE public.ai_access_status 
        DROP COLUMN code;
        RAISE NOTICE 'Dropped duplicate column code from ai_access_status table';
    ELSE
        RAISE NOTICE 'Column code_value already exists in ai_access_status table';
    END IF;
END $$;
