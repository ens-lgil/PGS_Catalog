from django.test import TestCase

class BrowseUrlTest(TestCase):
    """ Test the main URLs of the website """

    def test_urls(self):
        urls = [
            '/',
            '/browse/all/',
            '/browse/traits/',
            '/browse/studies/',
            '/browse/sample_set/',
            '/docs/',
            '/downloads/'
        ]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
