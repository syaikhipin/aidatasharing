-- Enable Row Level Security (RLS) for all public schema tables
-- This script addresses the RLS security warnings in PostgreSQL

-- Enable RLS on core application tables
ALTER TABLE public.schema_migrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.configuration_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mindsdb_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.configuration_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mindsdb_handlers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.database_connectors ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for system tables (admin-only access)
CREATE POLICY system_admin_only ON public.schema_migrations FOR ALL TO PUBLIC USING (false);
CREATE POLICY system_admin_only ON public.system_metrics FOR ALL TO PUBLIC USING (false);
CREATE POLICY system_admin_only ON public.configuration_overrides FOR ALL TO PUBLIC USING (false);
CREATE POLICY system_admin_only ON public.mindsdb_configurations FOR ALL TO PUBLIC USING (false);
CREATE POLICY system_admin_only ON public.configuration_history FOR ALL TO PUBLIC USING (false);
CREATE POLICY system_admin_only ON public.mindsdb_handlers FOR ALL TO PUBLIC USING (false);

-- Configuration table - allow read access but restrict write
CREATE POLICY configurations_read ON public.configurations FOR SELECT TO PUBLIC USING (true);
CREATE POLICY configurations_write ON public.configurations FOR INSERT TO PUBLIC WITH CHECK (false);
CREATE POLICY configurations_update ON public.configurations FOR UPDATE TO PUBLIC USING (false);
CREATE POLICY configurations_delete ON public.configurations FOR DELETE TO PUBLIC USING (false);

-- Organizations - allow read, restrict write based on user role
CREATE POLICY organizations_read ON public.organizations FOR SELECT TO PUBLIC USING (true);
CREATE POLICY organizations_write ON public.organizations FOR INSERT TO PUBLIC WITH CHECK (false);
CREATE POLICY organizations_update ON public.organizations FOR UPDATE TO PUBLIC USING (false);
CREATE POLICY organizations_delete ON public.organizations FOR DELETE TO PUBLIC USING (false);

-- Users - users can read their own data and organization members
CREATE POLICY users_own_data ON public.users FOR SELECT TO PUBLIC 
    USING (id = current_setting('app.current_user_id', true)::integer 
           OR organization_id = current_setting('app.current_org_id', true)::integer);
CREATE POLICY users_write ON public.users FOR INSERT TO PUBLIC WITH CHECK (false);
CREATE POLICY users_update ON public.users FOR UPDATE TO PUBLIC 
    USING (id = current_setting('app.current_user_id', true)::integer);
CREATE POLICY users_delete ON public.users FOR DELETE TO PUBLIC USING (false);

-- Datasets - users can access their own datasets and org shared ones
CREATE POLICY datasets_own_access ON public.datasets FOR SELECT TO PUBLIC 
    USING (owner_id = current_setting('app.current_user_id', true)::integer 
           OR organization_id = current_setting('app.current_org_id', true)::integer 
           OR sharing_level = 'public');
CREATE POLICY datasets_owner_write ON public.datasets FOR INSERT TO PUBLIC 
    WITH CHECK (owner_id = current_setting('app.current_user_id', true)::integer);
CREATE POLICY datasets_owner_update ON public.datasets FOR UPDATE TO PUBLIC 
    USING (owner_id = current_setting('app.current_user_id', true)::integer);
CREATE POLICY datasets_owner_delete ON public.datasets FOR DELETE TO PUBLIC 
    USING (owner_id = current_setting('app.current_user_id', true)::integer);

-- Dataset files - follow same rules as parent dataset
CREATE POLICY dataset_files_access ON public.dataset_files FOR SELECT TO PUBLIC 
    USING (dataset_id IN (
        SELECT id FROM datasets WHERE 
            owner_id = current_setting('app.current_user_id', true)::integer 
            OR organization_id = current_setting('app.current_org_id', true)::integer 
            OR sharing_level = 'public'
    ));
CREATE POLICY dataset_files_owner_write ON public.dataset_files FOR INSERT TO PUBLIC 
    WITH CHECK (dataset_id IN (
        SELECT id FROM datasets WHERE owner_id = current_setting('app.current_user_id', true)::integer
    ));
CREATE POLICY dataset_files_owner_update ON public.dataset_files FOR UPDATE TO PUBLIC 
    USING (dataset_id IN (
        SELECT id FROM datasets WHERE owner_id = current_setting('app.current_user_id', true)::integer
    ));
CREATE POLICY dataset_files_owner_delete ON public.dataset_files FOR DELETE TO PUBLIC 
    USING (dataset_id IN (
        SELECT id FROM datasets WHERE owner_id = current_setting('app.current_user_id', true)::integer
    ));

-- Database connectors - organization-level access
CREATE POLICY connectors_org_access ON public.database_connectors FOR SELECT TO PUBLIC 
    USING (organization_id = current_setting('app.current_org_id', true)::integer);
CREATE POLICY connectors_creator_write ON public.database_connectors FOR INSERT TO PUBLIC 
    WITH CHECK (created_by = current_setting('app.current_user_id', true)::integer);
CREATE POLICY connectors_org_update ON public.database_connectors FOR UPDATE TO PUBLIC 
    USING (organization_id = current_setting('app.current_org_id', true)::integer);
CREATE POLICY connectors_creator_delete ON public.database_connectors FOR DELETE TO PUBLIC 
    USING (created_by = current_setting('app.current_user_id', true)::integer);

-- Enable RLS on any additional tables that might exist
DO $$
DECLARE
    table_record RECORD;
BEGIN
    FOR table_record IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT IN (
            'schema_migrations', 'configurations', 'system_metrics', 
            'configuration_overrides', 'mindsdb_configurations', 
            'configuration_history', 'organizations', 'mindsdb_handlers', 
            'users', 'datasets', 'dataset_files', 'database_connectors'
        )
    LOOP
        EXECUTE 'ALTER TABLE public.' || table_record.tablename || ' ENABLE ROW LEVEL SECURITY';
        EXECUTE 'CREATE POLICY default_deny ON public.' || table_record.tablename || ' FOR ALL TO PUBLIC USING (false)';
    END LOOP;
END $$;

-- Grant necessary permissions to application role (if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_user;
        GRANT INSERT ON ALL TABLES IN SCHEMA public TO app_user;
        GRANT UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
        GRANT DELETE ON ALL TABLES IN SCHEMA public TO app_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
    END IF;
END $$;