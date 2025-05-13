-- Check if the column exists with the old name and rename it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_activation_codes' 
        AND column_name = 'code_value'
    ) AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_activation_codes' 
        AND column_name = 'code'
    ) THEN
        ALTER TABLE public.ai_activation_codes 
        RENAME COLUMN code_value TO code;
    END IF;
END $$;
