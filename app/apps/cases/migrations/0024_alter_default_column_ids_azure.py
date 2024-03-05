# Generated by Django 3.2.13 on 2024-02-08 13:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0023_add_multiple_tags"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                -- cases_casetheme
                IF NOT EXISTS (SELECT FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind = 'S' AND c.relname = 'cases_casetheme_id_seq' AND n.nspname = 'public') THEN
                    CREATE SEQUENCE public.cases_casetheme_id_seq INCREMENT BY 1 START WITH 1 MINVALUE 1 NO MAXVALUE CACHE 1;
                END IF;
            END
            $$;

            ALTER TABLE cases_casetheme ALTER COLUMN id SET DEFAULT nextval('public.cases_casetheme_id_seq'::regclass);
        """
        )
    ]