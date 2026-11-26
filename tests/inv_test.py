import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
from playwright.sync_api import sync_playwright

res=[]
def ok(n,c,d=''):res.append(c);print(('PASS ' if c else 'FAIL ')+n,d if not c else '')
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':1300,'height':900});errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT)
  pg.goto(APP_URL+'#budget');pg.wait_for_timeout(700)
  pg.click('.tabs a[href="#budget"]');pg.wait_for_timeout(300)
  # Landscaping actual is a button
  btn=pg.locator('button.actbtn[aria-label="Invoices for Landscaping"]')
  ok('landscaping actual is invoice button',btn.count()==1,btn.count())
  ok('shows invoice count','invoices' in btn.inner_text(),btn.inner_text() if btn.count() else '')
  btn.click();pg.wait_for_timeout(300)
  body=pg.locator('#pbody').inner_text()
  ok('title','Landscaping' in body and 'Invoices (' in body)
  ok('by type has Trade and Material',pg.locator('.kchip').count()==2)
  ok('totals',('$32,857.03' in body) and ('$24,116.44' in body),body[:300])
  # add an invoice
  pg.click('[data-act="p-showinv"]');pg.wait_for_timeout(100)
  pg.fill('#in-vendor','Test Trade Co');pg.fill('#in-no','T-1');pg.select_option('#in-kind','Trade');pg.fill('#in-amt','1000');pg.click('[data-act="p-invadd"]');pg.wait_for_timeout(200)
  body=pg.locator('#pbody').inner_text()
  ok('invoice added, invoiced up','$33,857.03' in body,body[:200])
  # pay partially linked
  row=pg.locator('#pbody .icard',has_text='Test Trade Co')
  row.locator('[data-act="p-invpay"]').click();pg.wait_for_timeout(200)
  sel=pg.locator('#pn-inv').input_value();ok('pay button preselects invoice',sel!='',sel)
  ok('placeholder is remaining 1000',pg.locator('#pn-amt').get_attribute('placeholder')=='1000',pg.locator('#pn-amt').get_attribute('placeholder'))
  pg.fill('#pn-amt','400');pg.click('[data-act="p-add"]');pg.wait_for_timeout(200)
  row=pg.locator('#pbody .icard',has_text='Test Trade Co')
  ok('invoice owed 600',('$600.00 DUE' in row.inner_text().upper()),row.inner_text())
  # pay remaining on that invoice
  row.locator('[data-act="p-invpay"]').click();pg.wait_for_timeout(200)
  pg.click('#pn-rest');pg.wait_for_timeout(200)
  row=pg.locator('#pbody .icard',has_text='Test Trade Co')
  ok('invoice paid',('PAID' in row.inner_text().upper() and 'DUE' not in row.inner_text().upper()),row.inner_text())
  # delete invoice -> payments unlinked
  row.locator('[data-act="p-invedit"]').click();pg.wait_for_timeout(100);pg.click('[data-act="p-invdel"]');pg.wait_for_timeout(100)
  pg.fill('#cmtype','delete');pg.click('#cmok');pg.wait_for_timeout(200)
  body=pg.locator('#pbody').inner_text()
  ok('after delete invoiced back','$32,857.03' in body)
  ok('unlinked payments shown','not tied to an invoice' in body.lower())
  # change an invoice type -> by type updates
  pg.click('[data-act="p-close"]');pg.wait_for_timeout(100)
  if pg.is_visible('#dmodal'): pg.click('#d-discard');pg.wait_for_timeout(150)
  # manage types
  pg.click('[data-act="t-open"]');pg.wait_for_timeout(200)
  tb=pg.locator('#tbody').inner_text()
  ok('types window lists test as not used',pg.locator('#tbody input[value="test"]').count()==1 and 'Not used' in tb)
  trow=pg.locator('#tbody tr',has=pg.locator('input[value="test"]'))
  trow.locator('[data-act="t-del"]').click();pg.wait_for_timeout(100);pg.fill('#cmtype','delete');pg.click('#cmok');pg.wait_for_timeout(200)
  ok('test type deleted',pg.locator('#tbody input[value="test"]').count()==0)
  ok('used types have no delete',pg.locator('#tbody tr',has=pg.locator('input[value="Landscaping"]')).locator('[data-act="t-del"]').count()==0)
  inp=pg.locator('#tbody input[value="Engineering review"]');inp.fill('Portable toilets');inp.dispatch_event('change');pg.wait_for_timeout(200)
  pg.click('[data-act="t-close"]');pg.wait_for_timeout(200)
  if pg.is_visible('#dmodal'): pg.click('#d-discard');pg.wait_for_timeout(150)
  ok('rename reflected in budget','Portable toilets' in pg.locator('#v-budget').inner_text())
  # backup mock
  pg.click('[data-act="bk-open"]');pg.wait_for_timeout(200);pg.click('[data-act="bk-now"]');pg.wait_for_timeout(800)
  calls=pg.evaluate("window.__calls.filter(c=>c[1]==='update_values').map(c=>[c[2].range,c[2].values.length])");print(calls)
  print('msg',pg.inner_text('#bkmsg'))
  ok('book tabs written',sum(1 for r,_ in calls if r.split('!')[0].replace(' (updating)','') in ("'Summary'","'Budget'","'Trade'","'Material'","'Service'","'Other'","'Read me'"))>=7 and not any(r.startswith("'Project files'") for r,_ in calls),calls)
  ok('backup finished',pg.inner_text('#bkmsg').startswith('Done'),pg.inner_text('#bkmsg'))
  st=pg.evaluate("window.__calls.filter(c=>c[1]==='update_spreadsheet').map(c=>c[2].requests.length)");print('update_spreadsheet calls',st)
  # mobile
  pg.set_viewport_size({'width':390,'height':800});pg.click('[data-act="bk-close"]');pg.locator('button.actbtn').first.click();pg.wait_for_timeout(200)
  ok('payments window no page overflow',pg.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'))
  ok('no script errors',not errs,errs)
  pg.screenshot(path=OUT+'/inv_mobile.png')
  pg.set_viewport_size({'width':1300,'height':900});pg.wait_for_timeout(200);pg.screenshot(path=OUT+'/inv_desk.png')
  b.close()
print(sum(res),'/',len(res))
