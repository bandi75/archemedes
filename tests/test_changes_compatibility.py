from archimedes.models.changes import ArtifactDiff, ChangeEvent, FieldDiff


def test_compatibility_module_exports_models():
    assert ChangeEvent is not None
    assert FieldDiff is not None
    assert ArtifactDiff is not None
