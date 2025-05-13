-- Check if we need to rename code_value to code in the ai_access_status table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_access_status' 
        AND column_name = 'code_value'
    ) AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_access_status' 
        AND column_name = 'code'
    ) THEN
        ALTER TABLE public.ai_access_status 
        RENAME COLUMN code_value TO code;
    END IF;
END $$;
