# Generated by Django 3.2.13 on 2024-02-08 15:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                -- events_caseevent
                IF NOT EXISTS (SELECT FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind = 'S' AND c.relname = 'events_caseevent_id_seq' AND n.nspname = 'public') THEN
                    CREATE SEQUENCE public.events_caseevent_id_seq INCREMENT BY 1 START WITH 1 MINVALUE 1 NO MAXVALUE CACHE 1;
                END IF;
            END
            $$;

            ALTER TABLE events_caseevent ALTER COLUMN id SET DEFAULT nextval('public.events_caseevent_id_seq'::regclass);
        """
        )
    ]