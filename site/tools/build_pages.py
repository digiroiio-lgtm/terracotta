#!/usr/bin/env python3
"""Build the TERRACOTTA website.

Sources
  templates/home.html   English homepage; its head, header, mega menu, pre-footer
                        and footer are the shell of every page (existing design).
  data/products.json    categories, products, colours, SEO titles.
  data/i18n.json        translations (keys are the English strings) and markets.

Output
  /en/, /de/, /fr/ ... one folder per active language with every page, plus a
  root index.html that sends visitors to their language, sitemap.xml and robots.txt.
  Run from anywhere:  python3 site/tools/build_pages.py
"""
import hashlib, html, json, os, re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(SITE, 'data/products.json'), encoding='utf-8'))
INDEX = open(os.path.join(SITE, 'templates/home.html'), encoding='utf-8').read()
I18N = json.load(open(os.path.join(SITE, 'data/i18n.json'), encoding='utf-8'))
SITEURL = D['siteUrl'].rstrip('/')
CATS = D['categories']
PRODS = D['products']
P = {p['sku']: p for p in PRODS}
CAT = {c['id']: c for c in CATS}
COLS = D['colours']
e = lambda s: html.escape(s, quote=True)
PENDING = 'To be confirmed with verified product data.'
FORMSPREE_ID = 'xgakokqp'
FORMSPREE_URL = 'https://formspree.io/f/' + FORMSPREE_ID
FORMSPREE_JS = 'assets/js/formspree-ajax-1.1.5.js'

# ------------------------------------------------------------------ shell
head_end = INDEX.index('<body')
HEAD = INDEX[:head_end]
HEAD = re.sub(r'\s*<link rel="preload" as="image"[^>]*>', '', HEAD)
HEAD = re.sub(r'\s*<link rel="canonical"[^>]*>', '', HEAD)
HEAD = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*"[^>]*>', '', HEAD)
HEAD = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', '', HEAD, flags=re.S)
hs = INDEX.index('<header class="">')
hv = INDEX.index('<div class="ae-video-container">', hs)
HEADER_NAV = INDEX[hs + len('<header class="">'):hv].replace(' aria-current="page"', '')
body_open = INDEX[INDEX.index('</head>') + len('</head>'):hs]
TAIL = INDEX[INDEX.rindex('\n', 0, INDEX.index('<div class="ae-section pre-footer-block')) + 1:]


def prefix_assets(s, prefix):
    s = re.sub(r'(?<=["\s,])assets/', prefix + 'assets/', s)
    return re.sub(r'href="css/', 'href="' + prefix + 'css/', s)


def bid(path, i):
    return 'block-' + hashlib.md5(f'{path}#{i}'.encode()).hexdigest()


def text_block(path, i, h2=None, paras=(), items=None, ctas=None, anchor=None, border=True, bg='ae-bg-grey', raw=''):
    out = []
    if h2:
        out.append(f'<h2{f" id=\"{anchor}\"" if anchor else ""}>{h2}</h2>')
    out += [f'<p>{p}</p>' for p in paras]
    if items:
        out.append('<ul>' + ''.join(f'<li>{x}</li>' for x in items) + '</ul>')
    if raw:
        out.append(raw)
    if ctas:
        out.append('<div class="ae-call-to-actions">' + ''.join(
            f'\n                <a class="btn btn-outline-primary" href="{u}" target="">{t}</a>' for t, u in ctas) + '\n            </div>')
    cls = 'ae-section ae-text-block' + (' ae-border-bottom' if border else '') + f' {bg}'
    inner = '\n            '.join(out)
    return f'''<div class="{cls}" id="{bid(path, i)}">
    <div class="ae-container ae-animate">
        <div class="ae-generic-text-container">
            {inner}
        </div>
    </div>
</div>
'''


def banner(path, i, title, ctas):
    btns = ''.join(f'\n            <a class="btn btn-outline-primary" href="{u}" target="">{t}</a>' for t, u in ctas)
    return f'''<div class="ae-section request-info-cta-block ae-bg-grey" id="request-info-cta-block-{bid(path, i)[6:]}">
    <div class="ae-banner-cta-container ae-animate">
        <div class="ae-container">
            <span class="h3">{title}</span>{btns}
        </div>
    </div>
</div>
'''


def field(name, label, kind='text', options=None, required=False, half=True, multiple=False):
    col = 'col-12 col-md-6' if half else 'col-12'
    req = ' required' if required else ''
    star = ' *' if required else ''
    if kind == 'select':
        opts = '<option value="">' + e(label) + star + '</option>'
        for o in options:
            if isinstance(o, tuple):
                opts += f'<optgroup label="{e(o[0])}">' + ''.join(f'<option value="{e(x)}">{e(x)}</option>' for x in o[1]) + '</optgroup>'
            else:
                opts += f'<option value="{e(o)}">{e(o)}</option>'
        ctl = f'<select class="form-select" id="f-{name}" name="{name}" aria-label="{e(label)}" data-fs-field{req}>{opts}</select>'
    elif kind == 'textarea':
        ctl = f'<textarea class="form-control" id="f-{name}" name="{name}" placeholder="{e(label)}{star}" aria-label="{e(label)}" data-fs-field{req}></textarea>'
    elif kind == 'file':
        ctl = (f'<label class="form-label" for="f-{name}">{e(label)}</label>'
               f'<input class="form-control" type="file" id="f-{name}" name="{name}"{" multiple" if multiple else ""} accept=".pdf,.dwg,.dxf,.jpg,.jpeg,.png" data-fs-field>')
    else:
        ctl = f'<input class="form-control" type="{kind}" id="f-{name}" name="{name}" placeholder="{e(label)}{star}" aria-label="{e(label)}" data-fs-field{req}>'
    return f'\n                    <div class="{col}">{ctl}<span data-fs-error="{name}"></span></div>'


def form_block(path, i, form_id, intro, fields, cta, subject, form_type, success, enctype=None):
    """Form posted to Formspree. Works as a plain HTML POST without JavaScript;
    with JavaScript the @formspree/ajax library submits it in place and shows the messages."""
    enc = f' enctype="{enctype}"' if enctype else ''
    return f'''<div class="ae-section ae-text-block ae-bg-grey" id="{bid(path, i)}">
    <div class="ae-container ae-animate">
        <div class="ae-generic-text-container">
            <div class="ae-form">
                <div class="ae-form-intro"><p>{intro}</p></div>
                <div data-fs-success>{success}</div>
                <div data-fs-error></div>
                <form class="row" id="{form_id}" method="POST" action="{FORMSPREE_URL}"{enc}>
                    <input type="hidden" name="_subject" value="{e(subject)}">
                    <input type="hidden" name="form_type" value="{e(form_type)}">
                    <input type="hidden" name="language" value="en">{''.join(fields)}
                    <div class="col-12 ae-form-buttons"><button type="submit" class="btn btn-outline-primary" data-fs-submit-btn>{cta}</button></div>
                </form>
            </div>
        </div>
    </div>
</div>
<script>
    window.formspree = window.formspree || function () {{ (formspree.q = formspree.q || []).push(arguments); }};
    formspree('initForm', {{ formElement: '#{form_id}', formId: '{FORMSPREE_ID}' }});
</script>
<script src="{FORMSPREE_JS}" defer></script>
'''


def crumbs(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": SITEURL + u} for i, (n, u) in enumerate([('Home', '/')] + items, 1)]}


ORG = {"@id": SITEURL + "/#organization"}


def page(path, title, desc, h1, body, schema, template='ae-template-genericpage', header_bg='ae-bg-grey', robots='index, follow'):
    i = body.find('<div class="ae-section request-info-cta-block')
    if i > 0:  # the banner has its own top border; avoid a double line
        j = body.rfind(' ae-border-bottom', 0, i)
        if j > 0:
            body = body[:j] + body[j + len(' ae-border-bottom'):]
    head = HEAD
    head = re.sub(r'<title>.*?</title>', f'<title>{e(title)}</title>', head, flags=re.S)
    head = re.sub(r'(<meta name="description" content=")[^"]*', r'\g<1>' + e(desc).replace('\\', r'\\'), head)
    head = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\g<1>' + e(title).replace('\\', r'\\'), head)
    head = re.sub(r'(<meta property="og:description" content=")[^"]*', r'\g<1>' + e(desc).replace('\\', r'\\'), head)
    ld = {"@context": "https://schema.org", "@graph": schema}
    head = head.replace('<meta name="robots" content="index, follow"/>',
                        f'<meta name="robots" content="{robots}"/>\n\t<link rel="canonical" href="{SITEURL}{path}"/>\n\t<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    doc = (head + f'<body class="{template}">' + body_open[body_open.index('>') + 1:]
           + f'<header class="ae-no-image {header_bg}">' + HEADER_NAV
           + f'''<div class="ae-header-container">
        <div class="ae-header-text">
            <h1>{h1}</h1>
        </div>
    </div>
</header>
            <main id="main-content">
''' + body + '</main>\n' + TAIL)
    DOCS[path] = (doc, robots)
    return path


DOCS = {}
built = []
colour_names = ', '.join(c['name'] for c in COLS)

# ------------------------------------------------------------------ product catalogue
path = '/product-catalogue/'
b = text_block(path, 0, None, ['Explore our complete collection of natural clay tile concepts, architectural formats and decorative surfaces. From floor tiles and outdoor pavers to pool details and artisan designs, discover the possibilities of terracotta.'])
for i, c in enumerate(CATS, 1):
    b += text_block(path, i, f'{c["number"]}. {e(c["name"])}', [e(c['description'])],
                    ctas=[(e(P[t]['shortName']), P[t]['url']) for t in c['types']] + [('View Collection', c['url'])])
b += text_block(path, 10, 'Twelve Colour References', ['A palette of twelve earthy colours inspired by clay, stone, nature and Mediterranean landscapes. Colour availability is confirmed for each product with verified product data.'],
                items=[f'<a href="{c["url"]}">{c["name"]}</a>' for c in COLS], ctas=[('Explore Colours', '/colour-collection/')])
b += text_block(path, 11, 'Technical Documentation', ['Technical information for each product will be published once verified. Visit the Technical Information page or contact our team for product enquiries.'],
                ctas=[('Technical Information', '/technical-information/')])
b += banner(path, 12, 'Interested in our collections?', [('Request a Quote', '/request-a-quote/'), ('Request Product Information', '/contacts/')])
built.append(page(path, 'Terracotta Product Catalogue | TERRACOTTA Collections',
                  'Explore the TERRACOTTA product catalogue featuring six collections, twelve product types and twelve earthy colour concepts.',
                  'The TERRACOTTA Product Catalogue', b,
                  [{"@type": "CollectionPage", "name": "The TERRACOTTA Product Catalogue", "url": SITEURL + path,
                    "hasPart": [{"@type": "CollectionPage", "name": c['name'], "url": SITEURL + c['url']} for c in CATS]},
                   crumbs([('Product Catalogue', path)])]))

# ------------------------------------------------------------------ colour collection
path = '/colour-collection/'
b = text_block(path, 0, None, ['Inspired by the natural world, the TERRACOTTA colour collection brings together twelve distinctive shades. From warm earthy neutrals to subtle mineral tones, each colour offers a different expression of natural clay.'])
b += text_block(path, 1, 'Twelve Shades of Earth', [], raw=''.join(f'<h3 id="{c["id"]}">{e(c["name"])}</h3><p>{e(c["description"])}</p>' for c in COLS))
b += text_block(path, 30, 'Colour Availability', ['Not every colour is available in every product type. Colour availability for each product will be confirmed with verified product data. Contact our team to discuss colours for your project.'],
                ctas=[('Explore Catalogue', '/product-catalogue/'), ('Request a Quote', '/request-a-quote/')])
built.append(page(path, 'Terracotta Tile Colours | Natural Earth Colour Collection',
                  'Explore twelve TERRACOTTA colour concepts inspired by natural clay, stone and Mediterranean landscapes. Discover earthy shades for architectural spaces.',
                  'The Colours of Earth', b,
                  [{"@type": "CollectionPage", "name": "The Colours of Earth", "url": SITEURL + path}, crumbs([('Colour Collection', path)])]))

# ------------------------------------------------------------------ custom artisan landing (mega menu card)
path = '/custom-artisan-tiles/'
ca = P['WL-CA']
b = text_block(path, 0, None, ['Discover distinctive terracotta designs and explore possibilities for customised architectural projects.', e(ca['productDescription'])],
               ctas=[('Discover More', ca['url']), ('Request a Quote', '/request-a-quote/')])
built.append(page(path, 'Custom Artisan Tiles | TERRACOTTA',
                  'Discover distinctive terracotta designs and explore possibilities for customised architectural projects with TERRACOTTA.',
                  'Custom Artisan Tiles', b,
                  [{"@type": "WebPage", "name": "Custom Artisan Tiles", "url": SITEURL + path}, crumbs([('Custom Artisan Tiles', path)])]))

# ------------------------------------------------------------------ categories
for c in CATS:
    path = c['url']
    b = text_block(path, 0, None, [e(c['description'])])
    for i, t in enumerate(c['types'], 1):
        p = P[t]
        b += text_block(path, i, e(p['productName']), [e(p['productDescription'])], ctas=[('Find Out More', p['url'])])
    b += text_block(path, 5, 'Colours', ['Explore twelve earthy shades in the TERRACOTTA Colour Collection. Colour availability for each product will be confirmed with verified product data.'],
                    ctas=[('Explore Colours', '/colour-collection/')])
    b += text_block(path, 6, 'Explore Other Collections', [], ctas=[(e(o['shortName']), o['url']) for o in CATS if o is not c])
    b += banner(path, 7, f'Interested in {e(c["name"])}?', [('Request a Quote', '/request-a-quote/'), ('Request Product Information', '/contacts/')])
    built.append(page(path, c['metaTitle'], c['description'], e(c['name']), b,
                      [{"@type": "CollectionPage", "name": c['name'], "url": SITEURL + path, "description": c['description'],
                        "hasPart": [{"@type": "Product", "name": P[t]['productName'], "url": SITEURL + P[t]['url']} for t in c['types']]},
                       crumbs([('Product Catalogue', '/product-catalogue/'), (c['name'], path)])]))

# ------------------------------------------------------------------ products
for p in PRODS:
    path = p['url']
    c = CAT[p['productCategory']]
    sib = [P[t] for t in c['types'] if t != p['sku']]
    idx = PRODS.index(p)
    related = sib + [PRODS[(idx + 2) % 12], PRODS[(idx + 6) % 12]]
    related = [x for i, x in enumerate(related) if x is not p and x not in related[:i]][:3]
    b = text_block(path, 0, None, [e(p['productDescription'])],
                   items=[f'Product category: <a href="{c["url"]}">{e(c["name"])}</a>', f'Product type: {e(p["productType"])}', f'Product reference: {p["sku"]}'])
    b += text_block(path, 1, 'Available Colours', [PENDING + ' Explore the full palette of twelve earthy shades in the Colour Collection.'], ctas=[('Explore Colours', '/colour-collection/')])
    b += text_block(path, 2, 'Dimensions, Surface &amp; Finish', [], items=[f'Available dimensions: {PENDING}', f'Surface and finish: {PENDING}'])
    b += text_block(path, 3, 'Product Specifications', ['Product specifications will be published after production validation.'], ctas=[('Technical Information', '/technical-information/')])
    b += text_block(path, 4, 'Suggested Applications', [e(p['suggestedApplications']) + ' Suitability for each application will be confirmed in the product documentation.'])
    b += text_block(path, 5, 'Related Products', [], ctas=[(e(r['shortName']), r['url']) for r in related] + [(f'Back to {e(c["shortName"])}', c['url'])])
    b += banner(path, 6, f'Interested in {e(p["productName"])}?', [('Request a Quote', '/request-a-quote/'), ('Request Product Information', '/contacts/')])
    built.append(page(path, p['metaTitle'], p['productDescription'], e(p['productName']), b,
                      [{"@type": "Product", "name": p['productName'], "description": p['productDescription'], "category": c['name'],
                        "brand": {"@type": "Brand", "name": "TERRACOTTA"}, "url": SITEURL + path},
                       crumbs([('Product Catalogue', '/product-catalogue/'), (c['name'], c['url']), (p['productName'], path)])]))

# ------------------------------------------------------------------ company
path = '/company/'
b = text_block(path, 0, 'Our Philosophy', ['TERRACOTTA is inspired by the relationship between earth, material and architecture.',
                                           'We believe natural surfaces have the power to bring warmth, individuality and character into the spaces we create.'])
b += text_block(path, 1, 'Inspired by Nature', ['Our design language draws inspiration from earthy colours, organic textures and Mediterranean architecture.'])
b += text_block(path, 2, 'A Timeless Material', ['Terracotta has a long architectural history. Its natural character continues to inspire contemporary spaces and distinctive design concepts.'],
                ctas=[('Materials &amp; Craft', '/materials-and-craft/')])
b += text_block(path, 3, 'Our Vision', ['To celebrate the expressive potential of natural clay through collections that connect material, design and architecture.'],
                ctas=[('Explore Catalogue', '/product-catalogue/'), ('Explore Colours', '/colour-collection/')])
built.append(page(path, 'About TERRACOTTA | The Art of Earth',
                  'Discover the TERRACOTTA philosophy, inspired by natural clay, architectural design and the timeless character of earth.',
                  'The Art of Earth', b, [{"@type": "AboutPage", "name": "About TERRACOTTA", "url": SITEURL + path, "about": ORG}, crumbs([('Company', path)])],
                  template='ae-template-companyinfo'))

# ------------------------------------------------------------------ projects
path = '/projects/'
b = text_block(path, 0, None, ['Explore architectural spaces and design concepts inspired by the natural character of terracotta. Discover how colour, texture and material selection contribute to distinctive environments.'])
b += text_block(path, 1, 'Explore by Setting', [], items=['Residential', 'Hospitality', 'Commercial', 'Outdoor Living', 'Landscape Architecture'])
b += text_block(path, 2, 'Project Portfolio', ['Project case studies will be published here once they are documented and authorised for publication.'],
                ctas=[('Explore Collections', '/product-catalogue/')])
b += banner(path, 3, 'Planning a project?', [('Contact Us', '/contacts/'), ('Request a Quote', '/request-a-quote/')])
built.append(page(path, 'Terracotta Architectural Projects | TERRACOTTA',
                  'Discover architectural and interior design projects featuring terracotta surfaces, natural materials and distinctive design concepts.',
                  'Projects &amp; Inspiration', b, [{"@type": "CollectionPage", "name": "Projects & Inspiration", "url": SITEURL + path}, crumbs([('Projects', path)])]))

# ------------------------------------------------------------------ magazine
path = '/magazine/'
b = text_block(path, 0, None, ['A collection of ideas, inspiration and perspectives exploring the relationship between architecture, natural materials and design.'])
b += text_block(path, 1, 'Editorial Categories', [], items=['Architecture &amp; Design', 'Terracotta &amp; Materials', 'Mediterranean Living', 'Interior Inspiration', 'Outdoor Spaces', 'Design Trends', 'Product Guides'])
b += text_block(path, 2, 'Coming Soon', [], items=['The Timeless Appeal of Terracotta in Architecture', 'How to Use Earth Tones in Contemporary Interiors',
                                                    'Terracotta and Mediterranean Architecture', 'Choosing Natural Clay Tiles for Interior Spaces',
                                                    'Designing Outdoor Spaces with Natural Materials', 'Understanding Terracotta Colours and Finishes',
                                                    'Decorative Tile Patterns in Modern Architecture', 'Terracotta in Hospitality and Boutique Hotel Design'],
                ctas=[('Explore Collections', '/product-catalogue/')])
built.append(page(path, 'Terracotta Magazine | Architecture, Materials & Design',
                  'Explore ideas, inspiration and editorial content about terracotta, architecture, natural materials and Mediterranean design.',
                  'The TERRACOTTA Magazine', b, [{"@type": "CollectionPage", "name": "The TERRACOTTA Magazine", "url": SITEURL + path}, crumbs([('Magazine', path)])]))

# ------------------------------------------------------------------ awards
path = '/awards/'
b = text_block(path, 0, None, ['Discover the design recognitions and achievements associated with TERRACOTTA.',
                               'Verified awards will be published here together with the award name, awarding organisation, year, recognised product or project and an official reference.'])
built.append(page(path, 'Design Awards & Recognition | TERRACOTTA',
                  'Explore verified design awards, recognitions and industry achievements associated with TERRACOTTA.',
                  'Awards &amp; Recognition', b, [{"@type": "WebPage", "name": "Awards & Recognition", "url": SITEURL + path}, crumbs([('Awards', path)])]))

# ------------------------------------------------------------------ contacts
path = '/contacts/'
cat_opts = [c['name'] for c in CATS]
b = text_block(path, 0, None, ['Whether you are an architect, designer, developer or distributor, we would be pleased to hear about your project.',
                               'Get in touch to explore our collections and discuss your requirements.'], border=False)
b += form_block(path, 1, 'contact-form', 'Fields marked * are required.', [
    field('full_name', 'Full Name', required=True), field('company', 'Company'),
    field('email', 'Email Address', 'email', required=True), field('country', 'Country', required=True),
    field('telephone', 'Telephone', 'tel'),
    field('enquiry_type', 'Enquiry Type', 'select', ['Product Information', 'Architectural Project', 'Custom Artisan Tiles', 'Distribution Partnership', 'General Enquiry'], required=True),
    field('product_category', 'Product Category', 'select', cat_opts), field('project_area', 'Estimated Project Area (m²)'),
    field('project_description', 'Project Description', 'textarea', half=False),
    field('additional_information', 'Additional Information', 'textarea', half=False)], 'Send Enquiry',
    'New enquiry – TERRACOTTA website', 'Contact', 'Thank you. Your enquiry has been sent and our team will be in touch.')
built.append(page(path, 'Contact TERRACOTTA | Product & Project Enquiries',
                  'Contact TERRACOTTA for product information, architectural projects, custom tile enquiries and distribution opportunities.',
                  'Let&#x27;s Talk About Your Project', b, [{"@type": "ContactPage", "name": "Contact TERRACOTTA", "url": SITEURL + path}, crumbs([('Contacts', path)])],
                  template='ae-template-genericpage'))

# ------------------------------------------------------------------ request a quote
path = '/request-a-quote/'
b = text_block(path, 0, None, ['Tell us about your project and the terracotta products you are interested in. Our team can review your requirements and help identify suitable collection options.'], border=False)
b += form_block(path, 1, 'quote-form', 'Fields marked * are required.', [
    field('name', 'Name', required=True), field('company', 'Company'),
    field('email', 'Email', 'email', required=True), field('country', 'Country', required=True),
    field('product_category', 'Product Category', 'select', cat_opts, required=True),
    field('product_type', 'Product Type', 'select', [(c['name'], [P[t]['productName'] for t in c['types']]) for c in CATS]),
    field('preferred_colour', 'Preferred Colour', 'select', [c['name'] for c in COLS]), field('preferred_dimensions', 'Preferred Dimensions'),
    field('estimated_quantity', 'Estimated Quantity (m²)'),
    field('project_type', 'Project Type', 'select', ['Residential', 'Hospitality', 'Commercial', 'Outdoor Living', 'Landscape Architecture', 'Other']),
    field('project_timeline', 'Project Timeline'),
    field('additional_information', 'Additional Information', 'textarea', half=False),
    field('drawings', 'Upload Drawings or Plans', 'file', half=False, multiple=True)], 'Submit Enquiry',
    'New quote request – TERRACOTTA website', 'Request a Quote', 'Thank you. Your quote request has been sent and our team will review your requirements.',
    enctype='multipart/form-data')
built.append(page(path, 'Request a Terracotta Tile Quote | TERRACOTTA',
                  'Request product information and a tailored quotation for your terracotta tile or architectural project.',
                  'Request a Quote', b, [{"@type": "ContactPage", "name": "Request a Quote", "url": SITEURL + path}, crumbs([('Request a Quote', path)])],
                  template='ae-template-genericpage'))

# ------------------------------------------------------------------ technical information
path = '/technical-information/'
b = text_block(path, 0, 'Product-Level Information', ['Verified technical information will be published for each product. It will cover:'],
               items=['Product reference', 'Dimensions and tolerances', 'Thickness', 'Weight', 'Water absorption', 'Slip resistance, where tested',
                      'Frost resistance, where tested', 'Surface finish', 'Application suitability', 'Installation requirements', 'Maintenance recommendations'])
b += text_block(path, 1, 'Related Information', [], ctas=[('Installation &amp; Care', '/installation-and-care/'), ('Materials &amp; Craft', '/materials-and-craft/'), ('Explore Catalogue', '/product-catalogue/')])
b += banner(path, 2, 'Need product information?', [('Request Product Information', '/contacts/')])
built.append(page(path, 'Terracotta Tile Technical Information | TERRACOTTA',
                  'Technical information for TERRACOTTA terracotta tiles: dimensions, thickness, surface finish, application suitability and maintenance.',
                  'Technical Information', b, [{"@type": "WebPage", "name": "Technical Information", "url": SITEURL + path}, crumbs([('Technical Information', path)])],
                  template='ae-template-technicalinformation'))

# ------------------------------------------------------------------ materials & craft
path = '/materials-and-craft/'
b = text_block(path, 0, None, ['Terracotta, meaning baked earth, is a material shaped by the relationship between clay, form and firing. Its natural tones and surface variations have made it a distinctive material in architecture for generations.',
                               'Explore the material character, colours, textures and finishes of terracotta.'],
               ctas=[('Explore Colours', '/colour-collection/'), ('Explore Catalogue', '/product-catalogue/')])
built.append(page(path, 'Natural Clay & Terracotta Craft | TERRACOTTA',
                  'Terracotta, meaning baked earth, is shaped by clay, form and firing. Explore the material character, colours, textures and finishes of terracotta.',
                  'The Material of Earth', b, [{"@type": "WebPage", "name": "The Material of Earth", "url": SITEURL + path}, crumbs([('Materials & Craft', path)])]))

# ------------------------------------------------------------------ installation & care
path = '/installation-and-care/'
b = text_block(path, 0, 'Guidance Topics', ['Installation and care guidance will cover the following topics. All technical recommendations will be checked against the relevant product documentation before publication.'],
               items=['Surface preparation', 'Substrate suitability', 'Installation guidance', 'Grouting', 'Sealing, where applicable', 'Cleaning', 'Maintenance', 'Product-specific recommendations'],
               ctas=[('Technical Information', '/technical-information/')])
b += banner(path, 1, 'Questions about installation?', [('Contact Us', '/contacts/')])
built.append(page(path, 'Terracotta Tile Installation & Care | TERRACOTTA',
                  'Installation and care guidance for TERRACOTTA terracotta tiles: surface preparation, installation, grouting, sealing, cleaning and maintenance.',
                  'Installation &amp; Care', b, [{"@type": "WebPage", "name": "Installation & Care", "url": SITEURL + path}, crumbs([('Installation & Care', path)])],
                  template='ae-template-technicalinformation'))

# ------------------------------------------------------------------ legal pages (placeholders, not indexed)
LEGAL = [('/privacy-policy/', 'Privacy Policy'), ('/legal-notice/', 'Legal Notice'), ('/cookie-policy/', 'Cookie Policy'),
         ('/general-sales-conditions/', 'General Sales Conditions'), ('/accessibility-statement/', 'Accessibility Statement'),
         ('/ethics-and-compliance/', 'Ethics and Compliance')]
for path, name in LEGAL:
    b = text_block(path, 0, None, ['This page will be published here before the website goes live.',
                                   'For any questions in the meantime, please contact our team.'], ctas=[('Contact Us', '/contacts/')])
    page(path, f'{name} | TERRACOTTA', f'{name} of TERRACOTTA | The Art of Earth.', name, b,
         [{"@type": "WebPage", "name": name, "url": SITEURL + path}, crumbs([(name, path)])], robots='noindex, follow')

# ------------------------------------------------------------------ homepage (English source)
DOCS['/'] = (INDEX, 'index, follow')

# ------------------------------------------------------------------ languages
LANGS = I18N['active']                      # e.g. ['en', 'de', 'fr']
MKT = I18N['markets']
T, HT = I18N['strings'], I18N['html']
norm = lambda t: re.sub(r'\s+', ' ', html.unescape(t)).strip()
url = lambda lang, path: f'{SITEURL}/{lang}{path}'
MISSING = {}


KEEP = set(I18N.get('keep', []))
PATTERNS = I18N.get('patterns', {})
TRANSLATED = {l: {norm(v[l]) for v in T.values() if l in v} | {norm(x) for v in HT.values() if l in v for x in re.split(r'<[^>]+>', v[l])} for l in LANGS}
SKU = re.compile(r'^[A-Z]{2,3}-[A-Z]{2}$')


def tr(text, lang):
    """Translate one English string (exact match, then patterns); record missing ones."""
    key = norm(text)
    if lang == 'en' or not key or key in KEEP or SKU.match(key):
        return None
    if key in T and lang in T[key]:
        return T[key][lang]
    if key in TRANSLATED.get(lang, ()):
        return None
    m = re.match(r'^(\d\d)\. (.+)$', key)
    if m:
        inner = tr(m.group(2), lang)
        return f'{m.group(1)}. {inner}' if inner else None
    for tpl, tl in PATTERNS.items():
        m = re.match('^' + re.escape(tpl).replace(re.escape('{}'), '(.+)') + '$', key)
        if m and lang in tl:
            g = m.group(1)
            inner = tr(g, lang) or (g if (g in KEEP or SKU.match(g)) else None)
            if inner is not None:
                return tl[lang].replace('{}', inner)
    if re.search('[A-Za-z]', key):
        MISSING.setdefault(lang, set()).add(key)
    return None


def translate(doc, lang):
    if lang == 'en':
        return doc
    for en, t in HT.items():
        if en in doc:
            doc = doc.replace(en, t[lang])

    def text(m):
        raw = m.group(1); t = tr(raw, lang)
        if t is None:
            return m.group(0)
        lead = raw[:len(raw) - len(raw.lstrip())]; trail = raw[len(raw.rstrip()):]
        return '>' + lead + html.escape(t, quote=False) + trail + '<'

    def attr(m):
        t = tr(m.group(2), lang)
        return m.group(0) if t is None else f' {m.group(1)}="{e(t)}"'
    head, body = doc[:doc.index('<body')], doc[doc.index('<body'):]
    parts = re.split(r'(<script.*?</script>|<option value="[^"]*")', body, flags=re.S)
    parts = [x if x.startswith('<script') or x.startswith('<option') else
             re.sub(r'\s(title|placeholder|aria-label|label)="([^"]*)"', attr, re.sub(r'>([^<>]+)<', text, x)) for x in parts]

    def meta(m):
        t = tr(m.group(2), lang)
        return m.group(0) if t is None else m.group(1) + e(t)
    head = re.sub(r'(<meta (?:name="description"|property="og:description"|property="og:title") content=")([^"]*)', meta, head)
    head = re.sub(r'(<title>)(.*?)(?=</title>)', lambda m: m.group(1) + (e(tr(m.group(2), lang)) if tr(m.group(2), lang) else m.group(2)), head, flags=re.S)

    def ld(m):
        data = json.loads(m.group(1))

        def walk(o, k=None):
            if isinstance(o, dict):
                return {kk: walk(v, kk) for kk, v in o.items()}
            if isinstance(o, list):
                return [walk(v, k) for v in o]
            if isinstance(o, str) and k in ('name', 'description', 'category'):
                return tr(o, lang) or o
            return o
        return '<script type="application/ld+json">' + json.dumps(walk(data), ensure_ascii=False) + '</script>'
    head = re.sub(r'<script type="application/ld\+json">(.*?)</script>', ld, head, flags=re.S)
    return head + ''.join(parts)


def hreflang(path):
    out = ''
    for l in LANGS:
        for code in MKT[l]['hreflang']:
            out += f'\n\t<link rel="alternate" hreflang="{code}" href="{url(l, path)}"/>'
    return out + f'\n\t<link rel="alternate" hreflang="x-default" href="{SITEURL}/"/>'


def localize(doc, lang, path, robots):
    doc = doc.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    extra = {'ko': ['css/fonts-ko.css'],                  # Korean glyphs from Noto Sans KR, Latin stays DM Sans
             'ar': ['css/fonts-ar.css']}.get(lang, [])     # Arabic glyphs from Noto Sans Arabic
    if MKT[lang].get('dir') == 'rtl':
        doc = doc.replace(f'<html lang="{lang}">', f'<html lang="{lang}" dir="rtl">', 1)
    if extra:
        doc = doc.replace('<link rel="stylesheet" href="css/fonts.css" />', '<link rel="stylesheet" href="css/fonts.css" />'
                          + ''.join(f'\n    <link rel="stylesheet" href="{x}" />' for x in extra), 1)
    if MKT[lang].get('dir') == 'rtl':  # right-to-left adjustments, loaded after all other stylesheets
        doc = doc.replace('<link rel="stylesheet" href="css/custom.css">', '<link rel="stylesheet" href="css/custom.css"><link rel="stylesheet" href="css/rtl.css">', 1)
    # internal links -> language folder (sitemap and language menu are handled separately)
    doc = re.sub(r'href="/(?!/)(?!sitemap\.xml)([^"]*)"', lambda m: f'href="/{lang}/{m.group(1)}"', doc)
    # language menu: same page in every active language, inactive languages removed
    doc = re.sub(r'\s*<li>\s*<a class="dropdown-item[^>]*>(\w\w)</a>\s*</li>', lambda m: m.group(0) if m.group(1) in LANGS else '', doc)
    doc = re.sub(r'\s*<a class="nav-link text-uppercase(?: active)?"\s*href="[^"]*">(\w\w)</a>', lambda m: m.group(0) if m.group(1) in LANGS else '', doc)

    def langlink(m):
        cls, code = m.group(1), m.group(3)
        cls = cls.replace(' active', '') + (' active' if code == lang else '')
        return f'{cls}"\n{m.group(2)}href="/{code}{path}">{code}</a>'
    doc = re.sub(r'(class="(?:dropdown-item|nav-link) text-uppercase(?: active)?)"\s*\n(\s*)href="[^"]*">(\w\w)</a>', langlink, doc)
    doc = doc.replace('ae-dropdown-toggle">en</button>', f'ae-dropdown-toggle">{lang}</button>')
    # head: canonical, hreflang, og:locale, structured data urls
    doc = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*"[^>]*>', '', doc)
    doc = re.sub(r'\s*<link rel="canonical"[^>]*>', '', doc)
    doc = doc.replace(f'<meta name="robots" content="{robots}"/>',
                      f'<meta name="robots" content="{robots}"/>\n\t<link rel="canonical" href="{url(lang, path)}"/>' + hreflang(path), 1)
    loc = f'<meta property="og:locale" content="{MKT[lang]["ogLocale"]}"/>' + ''.join(
        f'\n\t<meta property="og:locale:alternate" content="{a}"/>' for a in MKT[lang].get('ogLocaleAlternate', []))
    doc = re.sub(r'<meta property="og:locale" content="[^"]*"/>', loc, doc, count=1)
    doc = re.sub(r'<script type="application/ld\+json">(.*?)</script>', lambda m: '<script type="application/ld+json">' + re.sub(
        re.escape(SITEURL) + r'(/[^"#]*)(?=")', lambda u: url(lang, u.group(1)), m.group(1)) + '</script>', doc, flags=re.S)
    if path == '/' and lang in I18N.get('titles', {}):
        t = e(I18N['titles'][lang])
        doc = re.sub(r'<title>.*?</title>', f'<title>{t}</title>', doc, count=1, flags=re.S)
        doc = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\g<1>' + t, doc, count=1)
    if path == '/' and lang != 'en':
        doc = re.sub(r'(<a class="ae-header-logo" aria-label=")[^"]*', r'\g<1>' + e(T['Homepage'][lang]), doc, count=1)
    # search and forms
    doc = doc.replace('name="as_sitesearch" value="terracottaceramictiles.com"', f'name="as_sitesearch" value="terracottaceramictiles.com/{lang}"')
    doc = doc.replace('q=site%3Aterracottaceramictiles.com"', f'q=site%3Aterracottaceramictiles.com%2F{lang}"')
    doc = doc.replace('<input type="hidden" name="language" value="en">', f'<input type="hidden" name="language" value="{lang}">')
    depth = path.strip('/').count('/') + (2 if path != '/' else 1)
    return prefix_assets(doc, '../' * depth)


# ------------------------------------------------------------------ write pages
for lang in LANGS:
    for path, (doc, robots) in DOCS.items():
        out = os.path.join(SITE, lang, path.strip('/'), 'index.html')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf-8').write(localize(translate(doc, lang), lang, path, robots))

# ------------------------------------------------------------------ root: send visitors to their language
names = {l: MKT[l]['name'] for l in LANGS}
links = ''.join(f'<li><a href="/{l}/" hreflang="{l}" lang="{l}">{names[l]}</a></li>' for l in LANGS)
open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TERRACOTTA | The Art of Earth</title>
<meta name="description" content="TERRACOTTA | The Art of Earth. Choose your language.">
<link rel="icon" href="/assets/brand/favicon.ico" sizes="48x48">
<link rel="icon" href="/assets/brand/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png">{hreflang('/')}
<script>
(function () {{
  var langs = {json.dumps(LANGS)}, prefs = navigator.languages || [navigator.language || 'en'];
  for (var i = 0; i < prefs.length; i++) {{
    var l = (prefs[i] || '').slice(0, 2).toLowerCase();
    if (langs.indexOf(l) > -1) {{ location.replace('/' + l + '/'); return; }}
  }}
  location.replace('/en/');
}})();
</script>
<noscript><meta http-equiv="refresh" content="0; url=/en/"></noscript>
</head>
<body style="font-family:sans-serif;margin:2rem">
<p>TERRACOTTA | The Art of Earth</p>
<ul>{links}</ul>
</body>
</html>
''')

# ------------------------------------------------------------------ sitemap + robots
indexable = [p for p, (d, r) in DOCS.items() if r.startswith('index')]
open(os.path.join(SITE, 'sitemap.xml'), 'w').write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    + ''.join(f'  <url><loc>{url(l, p)}</loc>' + ''.join(
        f'<xhtml:link rel="alternate" hreflang="{c}" href="{url(x, p)}"/>' for x in LANGS for c in MKT[x]['hreflang'])
        + '</url>\n' for l in LANGS for p in indexable) + '</urlset>\n')
open(os.path.join(SITE, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITEURL}/sitemap.xml\n')

print(f'{len(DOCS)} pages x {len(LANGS)} languages built')
if MISSING:
    json.dump({l: sorted(v) for l, v in MISSING.items()}, open(os.path.join(SITE, 'data/i18n-missing.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('missing translations:', {l: len(v) for l, v in MISSING.items()}, '-> data/i18n-missing.json')
elif os.path.exists(os.path.join(SITE, 'data/i18n-missing.json')):
    os.remove(os.path.join(SITE, 'data/i18n-missing.json'))
