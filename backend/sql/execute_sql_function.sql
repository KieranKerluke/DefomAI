-- Create a function to execute SQL with parameters
-- This function should be run in Supabase SQL editor

CREATE OR REPLACE FUNCTION public.execute_sql(query text, params jsonb DEFAULT '[]'::jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result jsonb;
    param_values text[];
    i integer;
    sql_statement text;
BEGIN
    -- Extract parameters from jsonb array
    IF jsonb_typeof(params) = 'array' THEN
        param_values := array_fill(NULL::text, ARRAY[jsonb_array_length(params)]);
        FOR i IN 0..jsonb_array_length(params)-1 LOOP
            param_values[i+1] := params->i;
        END LOOP;
    END IF;
    
    -- Create the SQL statement with parameters
    sql_statement := query;
    
    -- Execute the query and get the result
    EXECUTE sql_statement INTO result USING param_values;
    
    -- Return the result
    RETURN result;
EXCEPTION
    WHEN OTHERS THEN
        RETURN jsonb_build_object(
            'error', SQLERRM,
            'detail', SQLSTATE
        );
END;
$$;

-- Create a function to generate activation codes
CREATE OR REPLACE FUNCTION public.generate_activation_code(admin_id uuid)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    code_value text;
    code_id uuid;
BEGIN
    -- Generate a random code (16 characters)
    code_value := upper(substring(md5(random()::text) from 1 for 16));
    code_id := gen_random_uuid();
    
    -- Insert into database
    INSERT INTO ai_activation_codes 
    (id, code_value, is_active, created_at, generated_by_admin_id, is_claimed)
    VALUES (code_id, code_value, true, now(), admin_id, false);
    
    -- Return the generated code
    RETURN code_value;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Failed to generate activation code: %', SQLERRM;
END;
$$;

-- Create the ai_activation_codes table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.ai_activation_codes (
    id uuid PRIMARY KEY,
    code_value text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    generated_by_admin_id uuid REFERENCES auth.users(id),
    is_claimed boolean NOT NULL DEFAULT false,
    claimed_by_user_id uuid REFERENCES auth.users(id),
    claimed_at timestamp with time zone
);

-- Create index on code_value for faster lookups
CREATE INDEX IF NOT EXISTS idx_ai_activation_codes_code_value ON public.ai_activation_codes(code_value);

-- Grant permissions
GRANT ALL ON public.ai_activation_codes TO postgres, service_role;
