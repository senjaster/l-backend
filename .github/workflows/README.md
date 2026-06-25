# GitHub Actions CI/CD

## Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| `test.yml` | Pull request (any branch) | Run pytest against a fresh Postgres container |
| `deploy.yml` | Push of a `v*` tag | Build image → run migrations → deploy to Yandex Cloud |

## How to release

```bash
git tag v0.3.6
git push origin v0.3.6
```

The pipeline will:
1. Build a `linux/amd64` Docker image tagged `v0.3.6`
2. Push it to Yandex Container Registry
3. Run Flyway migrations against the production database
4. Deploy a new Serverless Container revision pointing at the new image

## Required GitHub Secrets

Go to **Settings → Secrets and variables → Actions** in the repository and add:

| Secret | Description | How to get it |
|---|---|---|
| `YC_SA_JSON_KEY` | Service account JSON key (full file contents) | Yandex Cloud Console → IAM → Service Accounts → your SA → Create new key → JSON |
| `YC_SA_ID` | Service account ID (e.g. `aje...`) | Same page as above, the ID field |
| `YC_FOLDER_ID` | Yandex Cloud folder ID | Cloud Console → top breadcrumb, or `yc config list` |
| `FLYWAY_URL` | JDBC URL for production DB | e.g. `jdbc:postgresql://rc1b-xxx.mdb.yandexcloud.net:6432/db` |
| `FLYWAY_USER` | DB migration user | e.g. `l_app_admin` |
| `FLYWAY_PASSWORD` | DB migration password | From your DB credentials |

## Service account permissions

The service account used (`YC_SA_JSON_KEY`) needs the following roles in your Yandex Cloud folder:

| Role | Purpose |
|---|---|
| `container-registry.images.pusher` | Push images to Container Registry |
| `serverless.containers.admin` | Deploy new container revisions |

## Fixed values (already in the workflow)

| Variable | Value |
|---|---|
| Registry | `cr.yandex/crpd2b5gg7tt3399i6c9` |
| Image name | `t-app-backend` |
| Container ID | `bba55cg0j840ga866sb5` |
