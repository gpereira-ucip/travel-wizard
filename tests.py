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
    if 'leaflet.js' in u:  # Leaflet de prueba: registra qué mapas y teselas se piden
        return route.fulfill(content_type='application/javascript', body="window.__lf={maps:[],tiles:[]};window.__lf.icons=0;const _o={addTo(){return this},bindPopup(){return this},setIcon(){window.__lf.icons++;return this},setZIndexOffset(){return this}};window.L={map:(el)=>{window.__lf.maps.push(el.id);const m={fitBounds(){window.__lf.fits=(window.__lf.fits||0)+1;return m},setView(){return m},invalidateSize(){},remove(){}};return m},tileLayer:(u)=>{window.__lf.tiles.push(u);return {addTo(){return this}}},marker:()=>_o,polyline:()=>_o,divIcon:()=>({})};")
    if 'leaflet.css' in u: return route.fulfill(content_type='text/css', body='')
    if 'upload.wikimedia' in u or 'cartocdn' in u or 'tile.openstreetmap' in u: return route.fulfill(body=PNG, content_type='image/png')
    return route.abort()
mode=sys.argv[1] if len(sys.argv)>1 else 'live'
# v0.14 (mejora 15): contraste AA del texto sobre fondos lisos (claro y oscuro); los textos sobre fotos se miran en las capturas
AAJS=r"""(() => {const P=s=>{const m=s.match(/rgba?\(([^)]+)\)/);if(!m)return null;const a=m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);return [a[0],a[1],a[2],a.length>3?a[3]:1]};
 const L=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2])};
 const ov=(t,b)=>[0,1,2].map(i=>t[i]*t[3]+b[i]*(1-t[3])).concat(1);const out=[];const seen=new Set();
 const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
 while(n=w.nextNode()){const t=n.textContent.trim();if(!/[A-Za-zÁÉÍÓÚáéíóúñÑ0-9]/.test(t))continue;const el=n.parentElement;if(!el||seen.has(el))continue;seen.add(el);
  const r=el.getBoundingClientRect();if(r.width<1||r.height<1||r.bottom<0||r.top>innerHeight)continue;const cs=getComputedStyle(el);if(cs.visibility=='hidden')continue;
  if(el.closest('svg,[aria-hidden=true],.leaflet-container,:disabled,.toast,.modal-bg,.sheet'))continue;
  let op=1,img=false,st=[];for(let e=el;e&&e.nodeType==1;e=e.parentElement){const c2=getComputedStyle(e);op*=+c2.opacity;if(c2.backgroundImage!='none')img=true;const c=P(c2.backgroundColor);if(c&&c[3]>0&&!(st.length&&st[st.length-1][3]>=1))st.push(c)}
  if(img||op==0)continue;let bg=[255,255,255,1];for(let i=st.length-1;i>=0;i--)bg=ov(st[i],bg);let fg=P(cs.color);fg[3]*=op;const f=ov(fg,bg);
  const a=L(f),b=L(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);const fs=parseFloat(cs.fontSize),big=fs>=24||(fs>=18.66&&+cs.fontWeight>=700);
  if(ratio<(big?3:4.5))out.push(t.slice(0,30)+' · '+ratio.toFixed(2)+' · '+cs.color+' sobre rgb('+bg.slice(0,3).map(Math.round)+')')}
 return out})()"""
# v0.16: el numerito de Alertas depende de la fecha; se fuerza uno (y una píldora «en viaje») para medir su contraste siempre
BADGE="(()=>{const t=document.querySelector('.tab[data-t=alertas]');if(t&&!t.querySelector('.badge')){const b=document.createElement('span');b.className='badge';b.textContent='3';t.appendChild(b)}const h=document.querySelector('.tab[data-t=alertas]')||document.body;if(!document.querySelector('.when-pill.now')){const w=document.createElement('span');w.className='when-pill now';w.textContent='En viaje';w.style.cssText='position:fixed;top:120px;left:10px;z-index:99';document.body.appendChild(w)}return !!document.querySelector('.tab .badge')})()"
def aa(pg,name):
    bad=[]
    for th in ['light','dark']:
        pg.evaluate(f"setTheme('{th}')"); pg.wait_for_timeout(350); h=pg.evaluate('document.documentElement.scrollHeight'); y=0
        while y<h:
            pg.evaluate(f'window.scrollTo(0,{y})'); pg.wait_for_timeout(60); bad+=[th+' · '+x for x in pg.evaluate(AAJS)]; y+=700
    pg.evaluate("setTheme('light')"); pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(200)
    bad=sorted(set(bad)); assert not bad, ('contraste AA en '+name, bad); return 0
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
    # v0.12 (mejora 13): estado vacío ilustrado sin viajes
    assert pg.query_selector('.tripsempty svg') and pg.query_selector('#esNew') and len(pg.query_selector_all('.tripsempty .es-steps li'))==3, 'inicio sin viajes ilustrado'
    pg.click('#esIdeas'); pg.wait_for_timeout(500); assert pg.query_selector('.ideas.pulse'), 'ver ideas'
    pg.query_selector('.tripsempty').scroll_into_view_if_needed(); pg.query_selector('.tripsempty').screenshot(path=f'shots/{mode}_0empty.png')
    pg.click('#esNew'); assert pg.query_selector('[data-mode=varios]'), 'armar mi primer viaje abre el asistente'
    pg.go_back(); pg.wait_for_timeout(300)
    pg.click('#newTrip')
    # v0.7: primero se elige uno o varios lugares; con varios hay recorridos sugeridos
    assert pg.query_selector('#orig') is None, 'el destino aparece antes de elegir uno o varios'
    pg.click('[data-mode=varios]'); pg.click('[data-reg="Europa"]'); pg.wait_for_timeout(150)
    assert len(pg.query_selector_all('.route'))>=5, 'recorridos sugeridos de Europa'
    pg.screenshot(path=f'shots/{mode}_1routes.png'); pg.click('[data-reg="Europa"]')
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
    # v0.12: viaje sin clima → estado vacío con «Buscar el clima»
    if mode=='live':
        assert not pg.query_selector('.wxempty') and pg.query_selector('.wxd'), 'con clima no hay estado vacío'
        pg.evaluate("cur.weather={}; renderPlan()"); assert pg.query_selector('.wxempty #wxRetry'), 'sin clima'
        pg.query_selector('.wxempty').screenshot(path=f'shots/{mode}_6wxempty.png')
        pg.click('#wxRetry'); pg.wait_for_selector('.wxd', timeout=8000); assert not pg.query_selector('.wxempty'), 'el clima se recupera'
        assert pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('tw.trips'))[0].weather).length")>0, 'clima guardado'
    else:
        assert pg.query_selector('.wxempty') and 'sin conexión' in pg.inner_text('.wxempty'), 'sin clima offline'
        pg.query_selector('.wxempty').screenshot(path=f'shots/{mode}_6wxempty.png')
        pg.click('#wxRetry'); pg.wait_for_function("document.querySelector('#wxRetry') && document.querySelector('#wxRetry').textContent.includes('Reintentar')", timeout=15000)
    if mode=='live':
        pg.wait_for_timeout(1200)
        assert pg.query_selector('#lm-all') and pg.query_selector('#lm-0') and pg.query_selector('#lm-1'), 'mapa del recorrido y uno por destino'
        assert len(pg.query_selector_all('#maps .legs li'))==1 and 'Praga → Viena' in pg.inner_text('#maps .legs'), 'tramos del recorrido'
        lf=pg.evaluate('window.__lf'); print('mapas', lf)
        assert len(pg.query_selector_all('details.lng'))==2, 'idioma y costumbres de Chequia y Austria'
        pg.click('details.lng >> nth=0 >> summary'); pg.wait_for_timeout(200)
        assert len(pg.query_selector_all('details.lng[open] .ph'))==12 and 'Děkuji' in pg.inner_text('details.lng[open]'), 'frases en checo'
        pg.query_selector('details.lng[open]').screenshot(path=f'shots/{mode}_6lang.png')
        assert set(lf['maps'])>={'lm-all','lm-0','lm-1'} and all('tile.openstreetmap.org' in t for t in lf['tiles']), 'mapas por destino con teselas de OSM'
        el=pg.query_selector('#maps'); el.scroll_into_view_if_needed(); pg.wait_for_timeout(300); el.screenshot(path=f'shots/{mode}_6maps.png')
    # swap & add booking
    pg.click('[data-swap]'); 
    for t in ['reservas','valijas','plata','alertas']:
        pg.click(f'.tab[data-t={t}]'); pg.wait_for_timeout(400)
        if t=='reservas':
            assert pg.query_selector('.bkempty #esMail') and pg.query_selector('.bkempty #esAdd'), 'reservas vacías ilustradas'
            pg.screenshot(path=f'shots/{mode}_7bkempty.png')
            pg.click('#esMail'); pg.wait_for_timeout(200); assert pg.query_selector('#mailTxt'), 'subir mail desde el estado vacío'; pg.click('.modal [data-close] >> nth=0'); pg.wait_for_timeout(200)
            pg.click('#esAdd'); pg.fill('#b_title','Aerolíneas AR1132'); pg.fill('#b_from','EZE'); pg.fill('#b_to','PRG'); pg.fill('#b_time','22:30'); pg.fill('#b_code','abc123')
            pg.screenshot(path=f'shots/{mode}_7bkform.png'); pg.click('#b_save'); pg.wait_for_timeout(300)
            pg.click('.tab[data-t=reservas]'); pg.wait_for_timeout(300)
            assert not pg.query_selector('.bkempty') and pg.query_selector('.card.list .bk'), 'con una reserva ya no está vacío'
            pg.click('#addBk'); pg.click('[data-bt=hotel]'); pg.fill('#b_title','Hotel Golden Well'); pg.fill('#b_endDate', pg.eval_on_selector('#b_date','e=>e.value')); pg.click('#b_save'); pg.wait_for_timeout(300); pg.click('.tab[data-t=reservas]'); pg.wait_for_timeout(300)
        pg.screenshot(path=f'shots/{mode}_8{t}.png', full_page=True)
    ow=pg.evaluate('document.documentElement.scrollWidth'); print('scrollWidth',ow)
    for t in ['plan','reservas','valijas','plata','alertas']:
        pg.click(f'.tab[data-t={t}]'); pg.wait_for_timeout(500); assert pg.evaluate(BADGE), 'numerito de alertas'; aa(pg,t)
    assert pg.evaluate("(()=>{const b=document.querySelector('.tab .badge');return getComputedStyle(b).backgroundColor})()")=='rgb(176, 66, 42)', 'numerito de alertas en coral firme'
    assert pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--teal-ink').trim()")=='#1b7268', 'tokens de texto AA'
    print('contraste AA ok (5 pestañas, claro y oscuro)')
    # v0.9: buscador global (mejora 10)
    pg.click('#searchBtn'); pg.wait_for_selector('#sq'); pg.wait_for_timeout(150)
    assert len(pg.query_selector_all('[data-sv]'))>=1, 'viajes sugeridos con la búsqueda vacía'
    pg.screenshot(path=f'shots/{mode}_8bsearch0.png')
    pg.fill('#sq','ABC123'); pg.wait_for_timeout(150)
    assert 'Aerolíneas AR1132' in pg.inner_text('#sOut') and pg.query_selector('#sOut mark'), 'reserva por código'
    pg.screenshot(path=f'shots/{mode}_8csearch.png')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    assert pg.query_selector('.tab.on[data-t=reservas]') and pg.query_selector('.bk.hit'), 'lleva a la reserva resaltada'
    pg.screenshot(path=f'shots/{mode}_8dhit.png')
    pg.click('#searchBtn'); pg.fill('#sq','praga castillo'); pg.wait_for_timeout(150)
    if mode=='live':
        assert 'Castillo de Praga' in pg.inner_text('#sOut'), 'actividad'
        pg.click('#sOut [data-si]:has-text("Castillo de Praga") >> nth=0'); pg.wait_for_timeout(500)
        assert pg.query_selector('.tab.on[data-t=plan]') and pg.query_selector('.it.hit'), 'lleva a la actividad'
    else: pg.keyboard.press('Escape')
    pg.click('#searchBtn'); pg.fill('#sq','cargador'); pg.wait_for_timeout(150)
    assert 'valija' in pg.inner_text('#sOut').lower(), 'ítem de valija'
    pg.keyboard.press('Enter'); pg.wait_for_timeout(500); assert pg.query_selector('label.hit'), 'valija resaltada'
    pg.click('#searchBtn'); pg.fill('#sq','zzqx'); pg.wait_for_timeout(150); assert 'No encontré' in pg.inner_text('#sOut')
    pg.fill('#sq','día 2'); pg.wait_for_timeout(150); assert 'Día 2' in pg.inner_text('#sOut'); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    assert pg.query_selector('article.day.hit'), 'día resaltado'
    print('scrollWidthSearch', pg.evaluate('document.documentElement.scrollWidth'))
    pg.click('.tab[data-t=plan]'); pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_9planbk.png', full_page=True)
    pg.click('#themeBtn'); pg.wait_for_timeout(400); pg.screenshot(path=f'shots/{mode}_10dark.png')
    pg.click('#themeBtn'); pg.evaluate('window.scrollTo(0,0)')
    # v0.5: resumen, editar, duplicar
    pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_11summary.png')
    pg.click('#editTrip'); pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_12edit.png')
    pg.click('[data-en="0"][data-d="-1"]'); pg.fill('#e_name','Europa en familia'); pg.click('[data-ei=shopping]'); pg.click('#e_save'); pg.wait_for_timeout(1200)
    assert 'Europa en familia' in pg.inner_text('.thero h1')
    nd=pg.evaluate('cur.days.length'); print('days after edit',nd)
    # v0.15 (mejora 16): color de acento por viaje
    NIGHT="getComputedStyle(document.documentElement).getPropertyValue('--night').trim()"
    assert pg.evaluate(NIGHT)=='#14213d' and not pg.evaluate("document.documentElement.classList.contains('acc')"), 'viaje sin color = noche y dorado'
    pg.click('#editTrip'); pg.wait_for_timeout(300); assert len(pg.query_selector_all('[data-eacc]'))==6 and pg.query_selector('[data-eacc=clasico].on'), 'selector de 6 colores'
    pg.click('[data-eacc=lavanda]'); assert pg.evaluate(NIGHT)=='#2a1f4a', 'vista previa al tocar'
    pg.query_selector('.accs').scroll_into_view_if_needed(); pg.screenshot(path=f'shots/{mode}_12bacc.png')
    pg.click('.modal [data-close] >> nth=0'); pg.wait_for_timeout(200); assert pg.evaluate(NIGHT)=='#14213d', 'cancelar vuelve al color guardado'
    pg.click('#editTrip'); pg.wait_for_timeout(300); pg.click('[data-eacc=selva]'); pg.click('#e_save'); pg.wait_for_timeout(600)
    assert pg.evaluate("cur.accent")=='selva' and pg.evaluate("JSON.parse(localStorage.getItem('tw.trips')).find(t=>t.id===cur.id).accent")=='selva', 'color guardado'
    assert pg.evaluate(NIGHT)=='#12372a', 'el viaje se tiñe de Selva'
    pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_12cselva.png')
    pg.evaluate(BADGE); aa(pg,'viaje con color Selva'); pg.click('.tab[data-t=valijas]'); pg.wait_for_timeout(400); aa(pg,'valijas Selva'); pg.click('.tab[data-t=plan]'); pg.wait_for_timeout(300)
    pg.evaluate("setTheme('dark')"); pg.wait_for_timeout(300); pg.screenshot(path=f'shots/{mode}_12dselvadark.png'); pg.evaluate("setTheme('light')")
    # v0.17 (mejora 17): modo presentación
    pg.evaluate('window.scrollTo(0,0)'); pg.click('#presTrip'); pg.wait_for_timeout(700)
    nd=pg.evaluate('cur.days.length'); info=pg.evaluate("({n:document.querySelectorAll('#pres .ps').length,on:document.querySelector('#pres .ps.on').dataset.pi,c:document.querySelector('#pCount').textContent,bars:document.querySelectorAll('.pbars button').length,body:document.body.classList.contains('presing')})")
    print('pres', info); assert info['n']==nd+2 and info['on']=='0' and info['bars']==nd+2 and info['body'], 'presentación abre en la portada'
    pg.screenshot(path=f'shots/{mode}_23pcover.png')
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(650)
    d1=pg.evaluate("({on:document.querySelector('#pres .ps.on').dataset.pi,c:document.querySelector('#pCount').textContent,h:document.querySelector('#pres .ps.on h2').textContent,bg:getComputedStyle(document.querySelector('#pres .ps.on .pbg')).backgroundImage,li:document.querySelectorAll('#pres .ps.on .pl li').length})")
    print('pres day1', d1); assert d1['on']=='1' and d1['c']==f'Día 1 de {nd}' and d1['li']>=1, 'flecha → día 1'
    if mode=='live': assert 'url(' in d1['bg'], 'foto grande del día'
    pg.screenshot(path=f'shots/{mode}_23pday.png')
    assert not pg.evaluate(AAJS), 'contraste de la presentación'
    pg.click('#pres .ptap.nx'); pg.wait_for_timeout(300); assert pg.evaluate("PRES.i")==2, 'tocar a la derecha avanza'
    pg.click('#pres .ptap.pv'); pg.wait_for_timeout(300); assert pg.evaluate("PRES.i")==1, 'tocar a la izquierda retrocede'
    pg.mouse.move(320,500); pg.mouse.down(); pg.mouse.move(200,505); pg.mouse.move(60,510); pg.mouse.up(); pg.wait_for_timeout(300); assert pg.evaluate("PRES.i")==2, 'deslizar avanza'
    pg.mouse.move(60,500); pg.mouse.down(); pg.mouse.move(320,505); pg.mouse.up(); pg.wait_for_timeout(300); assert pg.evaluate("PRES.i")==1, 'deslizar retrocede'
    pg.click(f'.pbars [data-pgo="{nd+1}"]'); pg.wait_for_timeout(700); assert pg.evaluate("PRES.i")==nd+1 and pg.is_visible('#pres .ps.on [data-pgo="0"]'), 'saltar al final'
    pg.screenshot(path=f'shots/{mode}_23pend.png')
    pg.click('#pres .ps.on [data-pgo="0"]'); pg.wait_for_timeout(300); assert pg.evaluate("PRES.i")==0, 'ver de nuevo'
    pg.evaluate('PRES.dur=250'); pg.click('#pPlay'); pg.wait_for_timeout(700); pl=pg.evaluate("({i:PRES.i,play:document.querySelector('#pres').classList.contains('play'),b:document.querySelector('#pPlay').textContent})")
    print('pres play', pl); assert pl['i']>=2 and pl['play'] and pl['b']=='⏸', 'pasa solo'
    pg.click('#pPlay'); i0=pg.evaluate('PRES.i'); pg.wait_for_timeout(600); assert pg.evaluate('PRES.i')==i0, 'pausa'
    pg.evaluate('PRES.dur=7000'); pg.keyboard.press('End'); pg.wait_for_timeout(200); assert pg.evaluate('PRES.i')==nd+1; pg.keyboard.press('Home'); pg.wait_for_timeout(200); assert pg.evaluate('PRES.i')==0
    assert pg.evaluate('document.documentElement.scrollWidth')==390, 'presentación sin desborde'
    pg.evaluate("setTheme('dark')"); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(650); pg.screenshot(path=f'shots/{mode}_23pdaydark.png'); pg.evaluate("setTheme('light')")
    h0=pg.evaluate('location.hash'); pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    assert not pg.query_selector('#pres') and not pg.evaluate("document.body.classList.contains('presing')") and pg.evaluate('location.hash')==h0, 'Escape cierra la presentación'
    pg.click('#presTrip'); pg.wait_for_timeout(400); pg.go_back(); pg.wait_for_timeout(500)
    assert not pg.query_selector('#pres') and pg.query_selector('.thero') and pg.evaluate('location.hash')==h0, 'atrás cierra la presentación y queda en el viaje'
    pg.click('#presTrip'); pg.wait_for_timeout(400); pg.click('#pres [data-pclose] >> nth=-1'); pg.wait_for_timeout(400); assert not pg.query_selector('#pres') and pg.evaluate('location.hash')==h0, 'botón cerrar'
    pg.click('#dupTrip'); pg.wait_for_timeout(700); pg.screenshot(path=f'shots/{mode}_13dup.png'); pg.click('[data-close]')
    pg.click('#goHome'); pg.wait_for_timeout(400); pg.screenshot(path=f'shots/{mode}_14home.png', full_page=True)
    assert not pg.evaluate("document.documentElement.classList.contains('acc')") and pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--night').trim()")=='#14213d', 'el inicio vuelve a noche y dorado'
    assert pg.evaluate("[...document.querySelectorAll('.tripcard')].every(e=>getComputedStyle(e).getPropertyValue('--tacc').trim()=='#9fd36b' && getComputedStyle(e).boxShadow.includes('159, 211, 107'))"), 'tarjetas del viaje con su color'
    aa(pg,'inicio'); pg.emulate_media(contrast='more'); pg.wait_for_timeout(200)
    assert pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--muted').trim()")=='#3a4654', 'más contraste si el sistema lo pide'
    pg.emulate_media(contrast='no-preference')
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
    # v0.10: navegación por la URL y botón atrás (mejora 11)
    H=lambda: pg.evaluate('location.hash')
    assert H()=='#/nuevo/0', 'hash del asistente'
    pg.click('#wNext'); pg.wait_for_timeout(150); pg.click('#wNext'); pg.wait_for_timeout(150)
    assert H()=='#/nuevo/2', H()
    pg.go_back(); pg.wait_for_timeout(300)
    assert H()=='#/nuevo/1' and pg.evaluate('wz.step')==1, 'atrás vuelve al paso anterior'
    pg.click('#wBack'); pg.wait_for_timeout(300)
    assert H()=='#/nuevo/0' and pg.evaluate('wz.step')==0, 'botón atrás del asistente'
    pg.go_back(); pg.wait_for_timeout(300)
    assert H()=='#/' and pg.query_selector('#newTrip'), 'atrás sale del asistente al inicio'
    pg.click('.tripcard >> nth=0'); pg.wait_for_selector('.thero'); tid=pg.evaluate('cur.id')
    assert H()==f'#/viaje/{tid}/plan', H()
    pg.click('.tab[data-t=reservas]'); pg.wait_for_timeout(200); pg.click('.tab[data-t=valijas]'); pg.wait_for_timeout(200)
    assert H()==f'#/viaje/{tid}/valijas', H()
    pg.go_back(); pg.wait_for_timeout(300)
    assert H()==f'#/viaje/{tid}/plan' and pg.query_selector('.tab.on[data-t=plan]'), 'de una pestaña, atrás vuelve al itinerario'
    pg.click('#searchBtn'); pg.wait_for_selector('#sq'); pg.go_back(); pg.wait_for_timeout(300)
    assert not pg.query_selector('#sq') and pg.query_selector('.thero'), 'atrás cierra el buscador sin salir del viaje'
    pg.click('#editTrip'); pg.wait_for_timeout(200); pg.click('.modal [data-close] >> nth=0'); pg.wait_for_timeout(300)
    assert not pg.query_selector('.modal') and H()==f'#/viaje/{tid}/plan', 'cerrar la ventana no deja entradas de más'
    pg.click('#searchBtn'); pg.fill('#sq','cargador'); pg.wait_for_timeout(150); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    t1=pg.evaluate('cur.id'); assert H()==f'#/viaje/{t1}/valijas', ('el buscador lleva a la pestaña con su dirección', H())
    pg.go_back(); pg.wait_for_timeout(300); assert H()==f'#/viaje/{tid}/plan' and pg.evaluate('cur.id')==tid, H()
    pg.go_back(); pg.wait_for_timeout(300)
    assert H()=='#/' and pg.query_selector('#newTrip'), 'del viaje, atrás vuelve al inicio'
    pg.go_forward(); pg.wait_for_timeout(300); assert pg.query_selector('.thero') and pg.evaluate('cur.id')==tid, 'adelante'
    pg.click('#goHome'); pg.wait_for_timeout(300); pg.click('#goNews'); pg.wait_for_timeout(200); assert H()=='#/novedades'
    pg.go_back(); pg.wait_for_timeout(300); assert H()=='#/' and pg.query_selector('#newTrip'), 'atrás desde novedades'
    base=pg.evaluate("location.href.split('#')[0]")
    pg.goto(base+f'#/viaje/{tid}/plata'); pg.reload(); pg.wait_for_selector('.thero'); pg.wait_for_timeout(300)
    assert pg.query_selector('.tab.on[data-t=plata]') and pg.evaluate('cur.id')==tid, 'enlace directo a una pestaña'
    pg.screenshot(path=f'shots/{mode}_17bdeeplink.png')
    pg.goto(base+'#/viaje/noexiste/plan'); pg.reload(); pg.wait_for_timeout(500)
    assert H()=='#/' and pg.query_selector('#newTrip'), 'viaje inexistente vuelve al inicio'
    # v0.11 (mejora 12): transiciones entre pestañas y aparición escalonada
    pg.click(f'.tripcard[data-id="{tid}"]'); pg.wait_for_selector('.thero')
    assert pg.evaluate("document.querySelectorAll('.stg').length")>0, 'tarjetas escalonadas al entrar al viaje'
    pg.wait_for_timeout(1400); assert pg.evaluate("document.querySelectorAll('.stg,.tb-in').length")==0, 'las clases de animación se limpian'
    pg.click('.tab[data-t=valijas]')
    st=pg.evaluate("(()=>{const b=document.querySelector('#tabBody');return [b.classList.contains('tb-in'), b.style.getPropertyValue('--dir'), document.querySelector('.tind').style.getPropertyValue('--ti')]})()")
    assert st==[True,'1','2'], ('pestaña hacia la derecha', st)
    pg.wait_for_timeout(120); pg.screenshot(path=f'shots/{mode}_17cmid.png'); pg.wait_for_timeout(1300)
    pg.click('.tab[data-t=reservas]'); assert pg.evaluate("document.querySelector('#tabBody').style.getPropertyValue('--dir')")=='-1', 'pestaña hacia la izquierda'
    pg.wait_for_timeout(1300); pg.click('.tab[data-t=plan]'); pg.wait_for_timeout(1300)
    pg.click('[data-done="1:0"]'); assert pg.evaluate("document.querySelectorAll('.stg,.tb-in').length")==0, 'redibujar la misma pestaña no anima'
    pg.click('[data-done="1:0"]')
    pg.emulate_media(reduced_motion='reduce'); pg.click('.tab[data-t=alertas]')
    assert pg.evaluate("document.querySelectorAll('.stg,.tb-in').length")==0, 'reducir movimiento: sin animaciones'
    assert pg.evaluate("document.querySelector('.tind').style.getPropertyValue('--ti')")=='4'
    pg.emulate_media(reduced_motion='no-preference')
    pg.click('#goHome'); pg.click('#newTrip'); pg.click('[data-mode=uno]'); pg.wait_for_timeout(600); pg.go_back(); pg.wait_for_timeout(300)
    # v0.13 (mejora 14): escritorio / tablet horizontal en dos columnas con el mapa fijo
    pg.set_viewport_size({'width':1280,'height':900}); pg.click('#goHome'); pg.wait_for_timeout(300)
    pg.click(f'.tripcard[data-id="{tid}"]'); pg.wait_for_selector('#plan2'); pg.wait_for_timeout(1500)
    lay=pg.evaluate("(()=>{const d=document.querySelector('#days').getBoundingClientRect(),p=document.querySelector('#pside').getBoundingClientRect();return {cols:getComputedStyle(document.querySelector('#plan2')).gridTemplateColumns.split(' ').length,dr:d.right,pl:p.left,pos:getComputedStyle(document.querySelector('#pside')).position,nomap:document.querySelector('#plan2').classList.contains('nomap')}})()")
    print('desk layout', lay)
    if mode=='live':
        assert lay['cols']==2 and lay['dr']<=lay['pl'] and lay['pos']=='sticky' and not lay['nomap'], ('dos columnas', lay)
        assert len(pg.query_selector_all('.mapsw [data-msec]'))==3, 'selector de mapas: recorrido + 2 ciudades'
        pg.screenshot(path=f'shots/{mode}_19desk2col.png')
        pg.evaluate("window.scrollTo(0, document.querySelector('#days .day[data-di=\"2\"]').getBoundingClientRect().top+scrollY-200)"); pg.wait_for_timeout(500)
        st=pg.evaluate("[...document.querySelectorAll('#days .day.act')].map(a=>a.dataset.di).join(','), document.querySelector('#pside').getBoundingClientRect().top")
        st=pg.evaluate("({act:[...document.querySelectorAll('#days .day.act')].map(a=>a.dataset.di).join(','),top:Math.round(document.querySelector('#pside').getBoundingClientRect().top),sec:document.querySelector('.mapc.on').dataset.sec,lab:(document.querySelector('.mapc.on .mapday')||{}).textContent,icons:window.__lf.icons})")
        print('desk scroll', st)
        assert st['act']=='2' and st['sec']=='0' and 'Día 3' in st['lab'] and st['icons']>0 and st['top']<120, ('el mapa sigue al día', st)
        pg.screenshot(path=f'shots/{mode}_20deskscroll.png')
        last=pg.evaluate("cur.days.length-1"); lastStop=pg.evaluate("String(cur.days[cur.days.length-2].stop)")
        pg.evaluate(f"document.querySelector('#days .day[data-di=\"{last-1}\"] .dayh').click()"); pg.wait_for_timeout(200)
        assert pg.evaluate("document.querySelector('.mapc.on').dataset.sec")==lastStop, 'tocar un día cambia el mapa a su ciudad'
        pg.click('[data-msec=all]'); assert pg.evaluate("document.querySelector('.mapc.on').dataset.sec")=='all', 'chip Recorrido'
        pg.set_viewport_size({'width':1024,'height':768}); pg.wait_for_timeout(300)
        assert pg.evaluate("getComputedStyle(document.querySelector('#plan2')).gridTemplateColumns.split(' ').length")==2, 'tablet horizontal en dos columnas'
        print('scrollWidthTablet', pg.evaluate('document.documentElement.scrollWidth')); pg.screenshot(path=f'shots/{mode}_21tablet.png')
        pg.set_viewport_size({'width':390,'height':844}); pg.wait_for_timeout(300)
        mob=pg.evaluate("({cols:getComputedStyle(document.querySelector('#plan2')).display,maps:[...document.querySelectorAll('.mapc')].filter(s=>s.offsetHeight>0).length,chips:document.querySelector('.mapsw').offsetHeight})")
        assert mob['cols']=='block' and mob['maps']==3 and mob['chips']==0, ('en el celular todo sigue en una columna', mob)
        pg.set_viewport_size({'width':1280,'height':900}); pg.wait_for_timeout(300)
    else:
        pg.screenshot(path=f'shots/{mode}_19desk2col.png')
    pg.click('.tab[data-t=reservas]'); pg.wait_for_timeout(900); pg.screenshot(path=f'shots/{mode}_22deskres.png')
    print('scrollWidthDesk2', pg.evaluate('document.documentElement.scrollWidth'))
    pg.click('#goHome'); pg.wait_for_timeout(500); pg.screenshot(path=f'shots/{mode}_18desk.png')
    print('scrollWidthDesk', pg.evaluate('document.documentElement.scrollWidth'))
    print('ERRORS',errs)
    b.close()
