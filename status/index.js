import puppeteer from "@cloudflare/puppeteer";
const URLS = ["https://rvu-dash.streamlit.app", "https://prh-dash.streamlit.app"];
const HEADERS = { 
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36', 
    'upgrade-insecure-requests': '1', 
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8', 
    'accept-encoding': 'gzip, deflate, br', 
    'accept-language': 'en-US,en;q=0.9,en;q=0.8' 
};
async function capture(env) {
    const browser = await puppeteer.launch(env.MYBROWSER);
    for (let url of URLS) {
        console.log(`Fetching ${url}`)
        url = new URL(url).toString(); // normalize
        const page = await browser.newPage();
        await page.setExtraHTTPHeaders(HEADERS); 
        await page.goto(url, {"waitUntil": "networkidle0"});
        await page.screenshot();
    }
    await browser.close();
    return new Response(URLS.toString());
};

export default {
    async scheduled(controller, env, ctx) {
        res = capture(env);
        if (res.status != 200) {
            throw new Error(res);
        }
    },
    async fetch(request, env) {
        return capture(env);
    }
};
