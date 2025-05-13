-- Add updated_at column to ai_activation_codes table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_activation_codes' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.ai_activation_codes 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();
    END IF;
END $$;
