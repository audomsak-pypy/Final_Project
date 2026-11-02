from scripts.expected_values import checks
from app.queries import DB
import pytest
REFERENCE=checks(DB)
@pytest.mark.parametrize('case',REFERENCE,ids=[r['code']+'-'+r['label'] for r in REFERENCE])
def test_reference(case):
    assert case['actual']==case['expected'],case
