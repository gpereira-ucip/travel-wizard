import json, re, base64, sys, os, urllib.parse as up
# Uso: python3 tests.py [live|offline] [ruta/a/index.html]   (capturas en ./shots)
HTML=os.path.abspath(sys.argv[2] if len(sys.argv)>2 else 'index.html'); os.makedirs('shots',exist_ok=True)
from playwright.sync_api import sync_playwright
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
CITIES={'praga':('Praga','Chequia','CZ',50.0875,14.4214),'viena':('Viena','Austria','AT',48.2085,16.3721),'buenos aires':('Buenos Aires','Argentina','AR',-34.61,-58.38),'roma':('Roma','Italia','IT',41.9,12.5)}
PLACES=[('Castillo de Praga','castillo en Praga',90000),('Puente de Carlos','puente medieval',60000),('Museo Nacional','museo en Praga',50000),('Jardín Botánico de Praga','jardín botánico',20000),('Zoológico de Praga','zoológico',40000),('Mercado de Havelská','mercado',8000),('Catedral de San Vito','catedral gótica',70000),('Torre de Petřín','torre mirador',30000),('Estación central','estación de tren',30000),('Galería Nacional','galería de arte',35000),('Teatro Nacional','teatro',30000),('Palladium','centro comercial',9000),('Isla de Kampa','isla en el Moldava',15000),('Plaza de la Ciudad Vieja','plaza',80000),('Universidad Carolina','universidad',90000)]
def handle(route, req):
    u=req.url; q=dict(up.parse_qsl(up.urlparse(u).query))
    if 'geocoding-api' in u:
        n=q.get('name','').lower(); res=[]
        for k,(a,b,c,la,lo) in CITIES.items():
            if k.startswith(n[:4]): res.append(dict(name=a,country=b,country_code=c,admin1='',latitude=la,longitude=lo))
        return route.fulfill(json={'results':res})
    if 'api.php' in u and 'geosearch' in u:
        lat,lon=map(float,q['ggscoord'].split('|')); pages={}
        for i,(t,d,l) in enumerate(PLACES):
            pages[str(i)]=dict(pageid=i,title=t,description=d,length=l,thumbnail={'source':'https://upload.wikimedia.org/x%d.png'%i},coordinates=[{'lat':lat+(i%5-2)*.01,'lon':lon+(i%3-1)*.01}],fullurl='https://es.wikipedia.org/wiki/'+t)
        return route.fulfill(json={'query':{'pages':pages}})
    if 'api.php' in u and 'extracts' in u:
        ts=q['titles'].split('|'); return route.fulfill(json={'query':{'pages':{str(i):{'title':t,'extract':t+' es uno de los sitios más visitados de la ciudad. Tiene mucha historia.'} for i,t in enumerate(ts)}}})
    if 'rest_v1/page/summary' in u:
        return route.fulfill(json={'extract':'Ciudad hermosa con siglos de historia. Su casco antiguo es Patrimonio de la Humanidad desde hace varias décadas. Tiene más de cien torres y campanarios que se ven desde los miradores.','originalimage':{'source':'https://upload.wikimedia.org/hero.png'}})
    if 'open-meteo.com' in u:
        from datetime import date, timedelta
        s=date.fromisoformat(q['start_date']); e=date.fromisoformat(q['end_date']); n=(e-s).days+1
        t=[str(s+timedelta(i)) for i in range(n)]
        return route.fulfill(json={'daily':{'time':t,'weather_code':[(0,2,61,3)[i%4] for i in range(n)],'temperature_2m_max':[16+i%4 for i in range(n)],'temperature_2m_min':[5+i%3 for i in range(n)],'precipitation_sum':[(0,0,8,1)[i%4] for i in range(n)]}})
    if 'upload.wikimedia' in u or 'cartocdn' in u: return route.fulfill(body=PNG, content_type='image/png')
    return route.abort()
mode=sys.argv[1] if len(sys.argv)>1 else 'live'
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844})
    errs=[]; pg.on('console', lambda m: errs.append(m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None); pg.on('pageerror', lambda e: errs.append(str(e)))
    if mode=='live': pg.route('**/*', lambda r,req: r.continue_() if req.url.startswith('file:') else handle(r,req))
    else: pg.route('**/*', lambda r,req: r.continue_() if req.url.startswith('file:') else r.abort())
    pg.goto('file://'+HTML); pg.wait_for_timeout(600)
    pg.screenshot(path=f'shots/{mode}_0home.png')
    # v0.6: logo, favicon e ícono
    assert pg.evaluate("document.querySelector('#favIcon').href.startsWith('data:image/svg+xml')"), 'favicon'
    assert pg.query_selector('.brand svg.twlogo') and pg.query_selector('.hero .hero-logo'), 'logo'
    assert pg.query_selector('#nextFeat') is None
    pg.click('#newTrip')
    pg.fill('#orig','Buenos'); pg.wait_for_timeout(900); pg.click('#origS li')
    for c in ['Praga','Viena']:
        pg.fill('#dest',c); pg.wait_for_timeout(900); pg.click('#destS li'); pg.wait_for_timeout(200)
    pg.click('#stops [data-d="1"]'); pg.wait_for_timeout(100)
    pg.screenshot(path=f'shots/{mode}_1dest.png'); pg.click('#wNext')
    pg.screenshot(path=f'shots/{mode}_2dates.png'); pg.click('#wNext')
    pg.click('[data-g=familia]'); pg.fill('[data-tn="0"]','Gonzalo'); pg.fill('[data-tn="1"]','Daniela'); pg.fill('[data-tn="2"]','Joaquín')
    pg.screenshot(path=f'shots/{mode}_3trav.png'); pg.click('#wNext')
    for i in ['historia','cultura','ninos','gastronomia','naturaleza']: pg.click(f'[data-i={i}]')
    pg.screenshot(path=f'shots/{mode}_4int.png'); pg.click('#wNext')
    pg.fill('#bamt','6000'); pg.screenshot(path=f'shots/{mode}_5budget.png'); pg.click('#wNext')
    # v0.6: pantalla de carga del mago
    pg.wait_for_selector('#genScr', timeout=5000); pg.wait_for_timeout(450); pg.screenshot(path=f'shots/{mode}_5bgen.png')
    assert 'Praga y Viena' in pg.inner_text('#genScr h2'); assert pg.inner_text('#gtx').strip(), 'tip'
    if mode=='live': print('facts', pg.evaluate("document.querySelector('#gk').textContent"))
    pg.wait_for_selector('.thero', timeout=30000); pg.wait_for_timeout(800)
    pg.screenshot(path=f'shots/{mode}_6plan.png'); pg.screenshot(path=f'shots/{mode}_6planfull.png', full_page=True)
    # swap & add booking
    pg.click('[data-swap]'); 
    for t in ['reservas','valijas','plata','alertas']:
        pg.click(f'.tab[data-t={t}]'); pg.wait_for_timeout(400)
        if t=='reservas':
            pg.click('#addBk'); pg.fill('#b_title','Aerolíneas AR1132'); pg.fill('#b_from','EZE'); pg.fill('#b_to','PRG'); pg.fill('#b_time','22:30'); pg.fill('#b_code','abc123')
            pg.screenshot(path=f'shots/{mode}_7bkform.png'); pg.click('#b_save'); pg.wait_for_timeout(300)
            pg.click('.tab[data-t=reservas]'); pg.wait_for_timeout(300)
            pg.click('#addBk'); pg.click('[data-bt=hotel]'); pg.fill('#b_title','Hotel Golden Well'); pg.fill('#b_endDate', pg.eval_on_selector('#b_date','e=>e.value')); pg.click('#b_save'); pg.wait_for_timeout(300); pg.click('.tab[data-t=reservas]'); pg.wait_for_timeout(300)
        pg.screenshot(path=f'shots/{mode}_8{t}.png', full_page=True)
    ow=pg.evaluate('document.documentElement.scrollWidth'); print('scrollWidth',ow)
    pg.click('.tab[data-t=plan]'); pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_9planbk.png', full_page=True)
    pg.click('#themeBtn'); pg.wait_for_timeout(400); pg.screenshot(path=f'shots/{mode}_10dark.png')
    pg.click('#themeBtn'); pg.evaluate('window.scrollTo(0,0)')
    # v0.5: resumen, editar, duplicar
    pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_11summary.png')
    pg.click('#editTrip'); pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_12edit.png')
    pg.click('[data-en="0"][data-d="-1"]'); pg.fill('#e_name','Europa en familia'); pg.click('[data-ei=shopping]'); pg.click('#e_save'); pg.wait_for_timeout(1200)
    assert 'Europa en familia' in pg.inner_text('.thero h1')
    nd=pg.evaluate('cur.days.length'); print('days after edit',nd)
    pg.click('#dupTrip'); pg.wait_for_timeout(700); pg.screenshot(path=f'shots/{mode}_13dup.png'); pg.click('[data-close]')
    pg.click('#goHome'); pg.wait_for_timeout(400); pg.screenshot(path=f'shots/{mode}_14home.png', full_page=True)
    pg.click('#goNews'); pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_15news.png', full_page=True)
    pg.click('#backHome'); pg.click('#goBrands'); pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_16brands.png', full_page=True)
    # v0.6: logo en Para marcas + descarga
    assert len(pg.query_selector_all('.logos .twlogo'))==3
    with pg.expect_download() as dl: pg.click('[data-logo=icon]')
    assert dl.value.suggested_filename=='travel-wizard-icono.svg'
    pg.click('#backHome'); pg.wait_for_timeout(1200)
    assert pg.query_selector('#nextFeat'), 'proximo viaje destacado'
    pg.screenshot(path=f'shots/{mode}_16bhero.png')
    pg.click('#nextFeat'); pg.wait_for_selector('.thero'); pg.click('#goHome'); pg.wait_for_timeout(300)
    pg.click('[data-idea="2"]'); pg.wait_for_timeout(1500); pg.screenshot(path=f'shots/{mode}_17idea.png')
    print('idea stops', pg.evaluate('wz.stops.map(s=>s.name+":"+s.nights+":"+s.lat)'))
    ow2=pg.evaluate('document.documentElement.scrollWidth'); print('scrollWidth2',ow2)
    # escritorio
    pg.set_viewport_size({'width':1280,'height':900}); pg.click('#goHome'); pg.wait_for_timeout(500); pg.screenshot(path=f'shots/{mode}_18desk.png')
    print('scrollWidthDesk', pg.evaluate('document.documentElement.scrollWidth'))
    print('ERRORS',errs)
    b.close()
