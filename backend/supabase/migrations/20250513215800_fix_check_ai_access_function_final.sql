-- First drop the existing function
DROP FUNCTION IF EXISTS public.check_ai_access(UUID);

-- Then recreate it with the fixed parameter name and correct column names
CREATE OR REPLACE FUNCTION public.check_ai_access(input_user_id UUID)
RETURNS TABLE (
    has_access BOOLEAN,
    is_suspended BOOLEAN,
    is_blocked BOOLEAN,
    status TEXT,
    message TEXT,
    code_value TEXT
) AS $$
BEGIN
    -- Check if the user is an admin first
    IF EXISTS (
        SELECT 1 FROM auth.users
        WHERE id = input_user_id AND raw_user_meta_data->>'is_admin' = 'true'
    ) THEN
        -- Admins always have access
        RETURN QUERY SELECT 
            TRUE as has_access,
            FALSE as is_suspended,
            FALSE as is_blocked,
            'admin' as status,
            'Admin access granted' as message,
            NULL as code_value;
    ELSE
        -- Check the ai_access_status table
        RETURN QUERY 
        SELECT 
            aas.has_access,
            aas.is_suspended,
            aas.is_blocked,
            aas.status,
            aas.message,
            aas.code_value
        FROM public.ai_access_status aas
        WHERE aas.user_id = input_user_id
        UNION ALL
        -- If no record exists, return default values
        SELECT 
            FALSE as has_access,
            FALSE as is_suspended,
            FALSE as is_blocked,
            'no_access' as status,
            'No AI access. Please use an activation code.' as message,
            NULL as code_value
        WHERE NOT EXISTS (
            SELECT 1 FROM public.ai_access_status
            WHERE user_id = input_user_id
        )
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION public.check_ai_access(UUID) TO authenticated;
