-- Create a dedicated table for AI access status
CREATE TABLE public.ai_access_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    has_access BOOLEAN NOT NULL DEFAULT FALSE,
    is_suspended BOOLEAN NOT NULL DEFAULT FALSE,
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'no_access',
    message TEXT,
    code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add RLS policies
ALTER TABLE public.ai_access_status ENABLE ROW LEVEL SECURITY;

-- Users can read their own AI access status
CREATE POLICY "Users can read their own AI access status"
    ON public.ai_access_status FOR SELECT
    USING (auth.uid() = user_id);

-- Only admins can update AI access status
CREATE POLICY "Only admins can update AI access status"
    ON public.ai_access_status FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM auth.users
            WHERE auth.uid() = id AND raw_user_meta_data->>'is_admin' = 'true'
        )
    );

-- Create a function to check AI access status
CREATE OR REPLACE FUNCTION public.check_ai_access(user_id UUID)
RETURNS TABLE (
    has_access BOOLEAN,
    is_suspended BOOLEAN,
    is_blocked BOOLEAN,
    status TEXT,
    message TEXT,
    code TEXT
) AS $$
BEGIN
    -- Check if the user is an admin first
    IF EXISTS (
        SELECT 1 FROM auth.users
        WHERE id = user_id AND raw_user_meta_data->>'is_admin' = 'true'
    ) THEN
        -- Admins always have access
        RETURN QUERY SELECT 
            TRUE as has_access,
            FALSE as is_suspended,
            FALSE as is_blocked,
            'admin' as status,
            'Admin access granted' as message,
            NULL as code;
    ELSE
        -- Check the ai_access_status table
        RETURN QUERY 
        SELECT 
            aas.has_access,
            aas.is_suspended,
            aas.is_blocked,
            aas.status,
            aas.message,
            aas.code
        FROM public.ai_access_status aas
        WHERE aas.user_id = check_ai_access.user_id
        UNION ALL
        -- If no record exists, return default values
        SELECT 
            FALSE as has_access,
            FALSE as is_suspended,
            FALSE as is_blocked,
            'no_access' as status,
            'No AI access. Please use an activation code.' as message,
            NULL as code
        WHERE NOT EXISTS (
            SELECT 1 FROM public.ai_access_status
            WHERE user_id = check_ai_access.user_id
        )
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION public.check_ai_access(UUID) TO authenticated;
