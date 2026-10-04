from app.ingestion.manifest import project_root


def test_project_root_contains_apps_directory():
    assert (project_root() / "apps" / "api").exists()
