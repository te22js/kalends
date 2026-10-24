"""Test the standalone interface reference, not the user's Kalends application.
Requires Python, Playwright and a Chromium installation. No model/API calls.
Run: python tests/test_reference.py
"""
import json
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'04_INTERACTION_REFERENCE.html').read_text()
checks=[]

def check(name, condition, detail=''):
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
    if not condition: raise AssertionError(name+': '+detail)

with sync_playwright() as p:
    executable=shutil.which('chromium') or shutil.which('google-chrome')
    opts={'headless':True}
    if executable: opts['executable_path']=executable
    browser=p.chromium.launch(**opts)
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    errors=[]
    page.on('pageerror', lambda error:errors.append(str(error)))
    page.set_content(HTML,wait_until='load')
    check('Home and explicit fixture disclosure',page.get_by_text('Fictional frontend fixtures',exact=False).count()==1)
    check('No horizontal overflow at desktop',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
    page.screenshot(animations='disabled',path=str(ROOT/'evidence/reference_home_desktop.png'))
    page.get_by_role('button',name='Enter Pompeii',exact=False).click()
    check('Pompeii entry',page.get_by_role('heading',name='Aelia’s Pompeii').count()==1)
    page.screenshot(animations='disabled',path=str(ROOT/'evidence/reference_pompeii_desktop.png'))
    page.get_by_role('button',name='What happened to your order?',exact=True).click()
    check('One explicit ask advances the conversation',page.get_by_role('button',name='May I see your order?').is_visible())
    check('No modal after costless listening',not page.locator('dialog').evaluate('(d)=>d.open'))
    page.get_by_role('button',name='May I see your order?').click()
    check('Evidence remembered in fixture',page.get_by_text('You have Sabina’s order.',exact=False).count()>0)
    page.get_by_role('button',name='Pay for the market delivery',exact=False).click()
    check('Cost review opens before fixture mutation',page.locator('dialog').evaluate('(d)=>d.open') and page.locator('#coin-count').inner_text()=='6 coins')
    page.keyboard.press('Escape')
    check('Escape cancellation preserves coins',page.locator('#coin-count').inner_text()=='6 coins' and not page.locator('dialog').evaluate('(d)=>d.open'))
    check('Focus restored after Escape',page.evaluate("document.activeElement?.dataset.action === 'review-market'"))
    page.get_by_role('button',name='Pay for the market delivery',exact=False).click()
    page.get_by_role('button',name='Pay 3 coins',exact=True).click()
    check('Confirmed fixture payment once',page.locator('#coin-count').inner_text()=='3 coins')
    check('Result follows accepted fixture action',page.get_by_role('button',name='See the delivery').is_visible())
    page.get_by_role('button',name='Worlds',exact=True).click()
    page.get_by_role('button',name='Try the Observatory',exact=True).click()
    check('Unknown condition stays unknown before report',page.get_by_text('Rated capacity · Actual condition unknown',exact=True).is_visible())
    check('Private fixture result not pre-rendered',page.get_by_text('8 units reported available',exact=False).count()==0)
    page.get_by_role('button',name='Ask Mira for her report').click()
    check('Report changes available evidence',page.get_by_text('Mira’s report · Today, 00:00',exact=True).is_visible())
    for i in range(3): page.locator(f'#amount-{i}').fill('4')
    check('Conditional over-allocation warning',page.get_by_text('This is 4 more than Mira’s report supports.',exact=False).is_visible())
    page.locator('#promise-checkbox').check()
    page.get_by_role('button',name='Review allocation',exact=True).click()
    check('Reviewed promise included',page.locator('dialog').get_by_text('This also promises Lin four units.',exact=False).is_visible())
    page.get_by_role('button',name='Save allocation',exact=True).click()
    check('Nothing delivered by saving',page.get_by_role('button',name='Review and run the round',exact=True).is_visible() and page.locator('.ledger').count()==0)
    # Draft changes must not mutate accepted allocation or promise.
    page.locator('#amount-0').fill('1');page.locator('#promise-checkbox').uncheck()
    page.get_by_role('button',name='Review and run the round',exact=True).click()
    check('Settlement review uses saved allocation',page.locator('dialog').get_by_text('4 / 4 / 4',exact=False).count()==1)
    check('Settlement review uses saved promise',page.locator('dialog').get_by_text('Your promise to Lin will be checked',exact=False).count()==1)
    page.get_by_role('button',name='Run the round',exact=True).click()
    check('Capacity fixture executes 4/4/0',page.locator('.ledger tbody tr').nth(2).inner_text().replace('\n',' ').find('Lin')>=0 and page.locator('.ledger tbody tr').nth(2).locator('td').nth(2).inner_text()=='0')
    check('Missed saved promise explained',page.get_by_text('You promised Lin four units. That promise was not met.',exact=True).is_visible())
    check('Settled state removes pending-action copy',page.get_by_text('You can change it before running the round.',exact=True).count()==0 and page.get_by_text('Round settled.',exact=True).count()==1)
    check('No obsolete pending-action toast after settlement',page.locator('.toast').count()==0)
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(animations='disabled',path=str(ROOT/'evidence/reference_observatory_result.png'))
    page.get_by_role('button',name='Your story',exact=True).click()
    check('Both worlds have fixture chapters',page.get_by_role('heading',name='You paid for the market delivery.').is_visible() and page.get_by_role('heading',name='Your allocation became a result.').is_visible())
    page.get_by_role('button',name='Research',exact=True).click()
    check('Null result not concealed',page.get_by_role('heading',name='The candidate tied V3.').is_visible())
    page.get_by_role('button',name='Reset reference',exact=True).click()
    page.get_by_role('button',name='Reset reference',exact=True).last.click()
    page.get_by_role('button',name='Your story',exact=True).click()
    check('Reset clears only fixture history',page.get_by_role('heading',name='Your story has not started yet.').is_visible())
    page.get_by_role('button',name='Return to Pompeii',exact=True).click()
    page.get_by_role('button',name='Help',exact=True).click()
    page.keyboard.press('Tab')
    check('Dialog focus stays inside',page.locator('dialog').evaluate('(d)=>d.contains(document.activeElement)'))
    page.keyboard.press('Escape')
    for width in [390,768,1440]:
        page.set_viewport_size({'width':width,'height':844 if width==390 else 1000})
        for target in ['home','pompeii','observatory','story','research']:
            page.evaluate('(v)=>view(v)',target)
            check(f'No document overflow {target} at {width}px',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        if width==390:
            page.evaluate("view('pompeii')")
            page.screenshot(animations='disabled',path=str(ROOT/'evidence/reference_pompeii_narrow.png'),full_page=True)
    # Numeric error paths.
    page.evaluate("view('observatory')")
    page.locator('#amount-0').fill('12');page.locator('#amount-1').fill('12')
    page.get_by_role('button',name='Review allocation',exact=True).click()
    check('Over-rated allocation blocked',not page.locator('dialog').evaluate('(d)=>d.open'))
    page.locator('#amount-0').fill('-2')
    check('Negative fixture allocation normalized to zero',page.locator('#amount-0').input_value()=='0')
    page.emulate_media(reduced_motion='reduce')
    check('Reduced motion disables entry animation',page.evaluate("getComputedStyle(document.getElementById('app')).animationName==='none'"))
    check('No browser JavaScript errors',len(errors)==0,str(errors))
    browser_version=browser.version
    browser.close()
report={'scope':'Standalone design reference only; no Kalends repository/runtime access','browser':browser_version,'total_checks':len(checks),'passed':sum(c['passed'] for c in checks),'checks':checks,'not_tested':['User localhost:8823','Actual PlayCanvas rendering or movement','Agent cognition','Save/replay compatibility','Network and provider races','Human usability','Screen-reader use','Physical device performance']}
(ROOT/'evidence/REFERENCE_TEST_RESULTS.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'checks':len(checks),'passed':sum(c['passed'] for c in checks),'browser':browser_version},indent=2))
