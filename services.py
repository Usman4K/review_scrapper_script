from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pyppeteer import launch
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager


def get_date(date_str):
    date_list = date_str.split()
    unit = 1 if date_list[0] == "a" or date_list[0] == "an" else int(
        date_list[0])
    key = date_list[1]
    date_to_abs = datetime.now() - timedelta(days=5)
    if key in ["day", "days"]:
        date_to_abs = relativedelta(days=unit)
    elif key in ["week", "weeks"]:
        date_to_abs = relativedelta(weeks=unit)
    elif key in ["month", "months"]:
        date_to_abs = relativedelta(months=unit)
    elif key in ["year", "years"]:
        date_to_abs = relativedelta(years=unit)
    elif key in ["hour", "hours"]:
        date_to_abs = relativedelta(hours=unit)
    elif key in ["minute", "minutes"]:
        date_to_abs = relativedelta(minutes=unit)
    elif key in ["second", "seconds"]:
        date_to_abs = relativedelta(seconds=unit)

    return datetime.now() - date_to_abs


async def scrape_reviews(url):
    path = ChromeDriverManager().install()
    """Google Review Scraper gives you the ability to provide you the newest reviews based on
    location url. It suppose that url land directly to the location instead of providing related places.
    If all things go smoothly it returns data else show exception in terminal.

    Args:
        url (str): complete url with host and path as location

    Returns:
        list :  [flag, List of top 10 newest reviews object as HTML Or Exception Text]

    """

    # browser = await launch()  # without Browser Windoew display
    browser = await launch(
        headless=False,
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False,
        executablePath=path,
        args=['--no-sandbox']
    )
    print("browser Oppened..")
    page = await browser.newPage()

    try:
        await page.setViewport({'width': 1920, 'height': 1280})
        await page.goto(url)
        # Wait for the "Tabs Row" to appear on the page
        await page.waitFor(500)
        await page.waitForSelector(".yx21af.XDi3Bc", {'visible': True})
        # Wait for the "Reviews" button
        await page.waitForSelector(".EIgkw.OyjIsf")
        # Click the "Reviews" button
        await page.click('button[data-tab-index="1"]')
        # Wait for the "Reviews to Load"
        await page.waitFor(500)
        await page.waitForSelector(".OyjIsf.zemfqc")
        # Click the "Reviews" button
        await page.click('button[data-value="Sort"]')
        # Wait for the "Action Menu"
        await page.waitFor(500)
        await page.waitForSelector('.fxNQSd')
        # Click the "Newest" button
        await page.waitFor(500)
        await page.click('div[data-index="1"]', {'visible': True})

        # scroll view until last review dated more than 1 day --------------------------------
        while True:
            # Wait for the "Reviews to Load"
            await page.waitForSelector(".jJc9Ad")
            time_posted = await page.evaluate('''
                var elements = document.querySelectorAll(".jJc9Ad");
                var dated = elements[elements.length - 1].querySelector(".rsqaWe").textContent;
                dated''',
                                              force_expr=True)
            dated = time_posted.split()

            if "days" in dated or "week" in dated or "weeks" in dated or "month" in dated or "months" in dated or "years" in dated or "year" in dated:
                break

            else:
                await page.waitFor(500)
                await page.evaluate('''
                                    var reviewsSection = document.querySelector(".m6QErb.DxyBCb.kA9KIf.dS8AEf");
                                    reviewsSection.scrollTop = reviewsSection.scrollHeight;
                                    ''')

        # Wait for the "Reviews to Load"
        await page.waitForSelector(".jJc9Ad")

        # Evaluate the JS to extract content (innerText or innerHTML)
        await page.evaluate(

            '''
            var texts = [];
            var more_text = document.querySelectorAll(".w8nwRe.kyuRq");
            if (more_text) {
                for (var i = 0; i < more_text.length; i++) { 
                more_text[i].click();
                }
            }''', force_expr=True)

        content = await page.evaluate('''
            var elements = document.querySelectorAll(".jJc9Ad");
            for (var i = 0; i < elements.length; i++) {
                const dated = elements[i].querySelector(".rsqaWe").textContent;
                texts.push(elements[i].innerHTML);

            }
            texts''',

                                      force_expr=True)

        return [True, content]
    except Exception as e:
        return [False, str(e)]

    finally:
        await browser.close()


def format_data(reviews_content_list):
    """Accept the list of reviews as html content and extract valuable data from it

    Args:
        reviews_content_list (list): List of Reviews obtained from Scraper Function

    Returns:
        list: List of dictionaries including name, review and dated key-value pairs
    """

    data_list = []

    # Loop through each HTML content and parse it
    for review_element in reviews_content_list:
        soup = BeautifulSoup(review_element, 'html.parser')

        # -----------------------Extract information from the parsed HTML -------------------------
        # Extract the name
        name = soup.find('div', class_='d4r55').get_text()
        google_review_id = soup.find(
            'button', class_='WEBjve').get("data-review-id")
        review = soup.find('span', class_="wiI7pd")
        review_post_time = soup.find('span', class_="rsqaWe").get_text()
        dated = get_date(review_post_time)
        rating_span = soup.find('span', class_="kvMYJc")
        rating = rating_span.get('aria-label')[0]
        if review:
            review = review.get_text()
        else:
            review = ""
        # Create a dictionary for the extracted information
        data_dict = {
            "id": google_review_id,
            "author": name,
            "content": review,
            "rating": rating,
            "datetime": dated.isoformat()
        }

        # Append the dictionary to the list
        data_list.append(data_dict)

    return data_list
