import invoke

db_service = "db"
db_user = "postgres"
db_database = "postgres"


@invoke.task
def psql(ctx, user=db_user, database=db_database):
    """psql is the PostgreSQL interactive terminal."""
    ctx.run(f"docker-compose exec {db_service} psql {database} {user}", pty=True)
