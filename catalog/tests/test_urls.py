from django.test import TestCase, Client

databases_list = ['default', 'benchmark']

class BrowseUrlTest(TestCase):
    """ Test the main URLs of the website """
    databases = databases_list

    def test_urls(self):
        client = Client()
        urls = [
            '/',
            '/about/',
            '/benchmark/',
            '/browse/all/',
            '/browse/traits/',
            '/browse/studies/',
            '/browse/sample_set/',
            '/docs/',
            '/downloads/',
            '/rest/',
            '/robots.txt'
        ]
        for url in urls:
            resp = client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_urls_redirection(self):
        client = Client()

        urls = [
            '/docs/curation',
            '/submit/',
            '/template/current'
        ]
        for url in urls:
            resp = client.get(url)
            self.assertEqual(resp.status_code, 302)
