from local_ai.project_context_detector import detect_project_switch, find_matching_project


class FakeProject:
    def __init__(self, id, name):
        self.id = id
        self.name = name


# ----------------------------------------------------------------
# detect_project_switch
# ----------------------------------------------------------------
def test_detects_trabajemos_en():
    assert detect_project_switch("Trabajemos en OmniLocal") == "OmniLocal"


def test_detects_activa_el_proyecto():
    assert detect_project_switch("activá el proyecto app diccionario") == "app diccionario"


def test_detects_cambiar_al_proyecto():
    assert detect_project_switch("cambiar al proyecto Tampermonkey") == "Tampermonkey"


def test_detects_cambiate_al_proyecto():
    assert detect_project_switch("cambiate al proyecto Fenix") == "Fenix"


def test_ignores_unrelated_text():
    assert detect_project_switch("Mi nombre es Marcelo") is None
    assert detect_project_switch("¿Qué proyectos tengo?") is None


def test_ignores_empty_text():
    assert detect_project_switch("") is None
    assert detect_project_switch("   ") is None


# ----------------------------------------------------------------
# find_matching_project
# ----------------------------------------------------------------
def test_finds_single_matching_project():
    projects = [FakeProject(1, "OmniLocal"), FakeProject(2, "app_diccionario")]
    match = find_matching_project(projects, "OmniLocal")
    assert match is not None
    assert match.id == 1


def test_no_match_returns_none():
    projects = [FakeProject(1, "OmniLocal")]
    assert find_matching_project(projects, "algo que no existe") is None


def test_ambiguous_match_returns_none():
    projects = [FakeProject(1, "OmniLocal Core"), FakeProject(2, "OmniLocal Mobile")]
    assert find_matching_project(projects, "OmniLocal") is None


def test_empty_project_list():
    assert find_matching_project([], "OmniLocal") is None
