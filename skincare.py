"""Concern-first educational routing. Not a diagnosis or treatment plan."""
import json
from pathlib import Path
CATALOG = json.loads((Path(__file__).parent/'catalog.json').read_text())

OPTIONS = {'concern': {'spots','dryness','tone','simple','painful'}, 'feel': {'dry','oily','combination','balanced','unsure'}, 'sensitivity': {'comfortable','reactive','irritated'}, 'routine': {'starting','basic','actives','prescribed'}, 'spf': {'daily','sometimes','none'}}

def recommend(a):
    if not isinstance(a,dict) or set(a)!=set(OPTIONS) or any(not isinstance(a[k],str) or a[k] not in v for k,v in OPTIONS.items()):
        raise ValueError('Please answer all five questions.')
    care=a['concern']=='painful' or a['sensitivity']=='irritated' or a['routine']=='prescribed'
    focus={'spots':('Support blemish-prone skin','Keep cleansing gentle. Scrubbing and picking can make irritation worse. A patch is an optional cover for an occasional surface spot, not an acne treatment plan.'), 'dryness':('Put moisture first','A comfortable routine starts with gentle cleansing and a moisturizer. A wash-off cleanser does not replace a leave-on moisturizer.'), 'tone':('Build a consistent foundation','Uneven tone and lingering marks have different causes. Prioritize daily sun protection; a cleanser or brush is not a treatment for dark marks.'), 'simple':('Start with the essentials','Keep your routine manageable: cleanse gently, moisturize, and protect your skin from the sun.'), 'painful':('Get personal guidance first','Deep or painful breakouts deserve an assessment from a dermatologist. A shopping quiz cannot identify the cause or choose treatment.')}[a['concern']]
    title,why=focus
    if a['sensitivity']=='reactive' and not care:
        title='Keep your routine gentle'
        why+=' Since products can bother your skin, choose fragrance-free options and introduce one new product at a time.'
    if care:
        title='Get personal guidance first'
        if a['sensitivity']=='irritated': why='With skin that is currently burning, raw, or persistently irritated, pause new product experiments and ask a healthcare professional for advice.'
        elif a['routine']=='prescribed': why='You already have a prescribed routine. Check additions with your prescriber instead of changing your treatment based on this quiz.'
    moisturizer={'dry':'Look for a fragrance-free cream to support dry-feeling skin.', 'oily':'Look for a lightweight moisturizer labeled non-comedogenic. Oily-feeling skin still needs moisture.', 'combination':'Try a lightweight moisturizer, adding more to areas that feel dry.', 'balanced':'Use a moisturizer that feels comfortable and does not irritate your skin.', 'unsure':'Start with a simple moisturizer you tolerate; you do not need a perfect skin-type label.'}[a['feel']]
    spf=('Keep your daily sun-protection habit. ' if a['spf']=='daily' else 'Make sun protection your next consistent habit. ')+ 'Choose broad-spectrum, water-resistant SPF 30 or higher, with shade and protective clothing outdoors.'
    routine={'starting':'Build the basics before adding extras.', 'basic':'Keep the products that already work for you; you do not need to replace your whole routine.', 'actives':'Avoid adding several active products at once. If your routine is irritating, ask a dermatologist for help simplifying it.', 'prescribed':'Keep following your prescribed plan and ask your prescriber before adding products.'}[a['routine']]
    patches=a['concern']=='spots' and a['sensitivity']=='comfortable' and a['routine']!='actives' and not care
    product={'name':'Pimple Rescue Patches','path':'/products/pimple-rescue-patch','image':'dl-patch-real-creator.jpg?v=1789329677','product_why':'An optional hydrocolloid cover for an occasional surface spot. It will not treat deep, painful, or persistent acne.'} if patches else {'name':'The Reset Cleanser','path':'/products/the-reset-cleanser','image':'dl-cleanser-sink.jpg?v=1789177321','product_why':'A fragrance-free cleanser option for the cleansing step. Review the ingredients and introduce it gradually; individual tolerance varies.'}
    bundle = []
    if not care:
        bundle.append(dict(CATALOG['items']['cleanser'], reason='For the cleansing step. Keep your current cleanser if it already works for you.'))
        if patches:
            bundle.append(dict(CATALOG['items']['patches'], reason='An optional cover for occasional surface spots, not treatment for deep or persistent acne.'))
            if a['routine']=='starting':
                bundle.append(dict(CATALOG['items']['towels'], reason='An optional fresh towel for gently patting dry. A clean reusable towel is also fine.'))
        elif a['concern']=='simple' and a['routine']=='starting':
            bundle.append(dict(CATALOG['items']['bands'], reason='A convenience extra to keep water off your wrists while you wash.'))
        else:
            bundle.append(dict(CATALOG['items']['towels'], reason='An optional fresh towel for gently patting dry. It is a convenience item, not a skin treatment.'))
    bundle_name='Your blemish-care bundle' if patches else 'Your gentle-care bundle' if a['sensitivity']=='reactive' else 'Your simple-start bundle' if a['concern']=='simple' else 'Your daily-care bundle'
    return dict(product,bundle=bundle,bundle_name=bundle_name,catalog_checked_at=CATALOG['checked_at'],key='professional-guidance' if care else a['concern'],title=title,why=why,care=care,steps=[['Cleanse gently','Use a gentle cleanser with your fingertips. Avoid scrubbing, especially when skin is reactive or breaking out.'],['Support moisture',moisturizer],['Protect during the day',spf]],routine_note=routine,shop='https://find-a-derm.aad.org/' if care else 'https://dermilogic.com'+product['path'],shop_label='Find a dermatologist' if care else 'Explore '+product['name'],gap='Moisturizer and sunscreen are separate essentials. We have not verified matching Dermilogic products for those steps, so choose suitable options you already trust.',notice='Seek prompt medical care for rapidly worsening symptoms, significant swelling, or signs of infection.' if care else 'If concerns persist, worsen, or become painful, see a dermatologist. This guide does not diagnose skin conditions or replace medical care.')
