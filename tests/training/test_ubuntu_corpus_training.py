from unittest.mock import Mock
from io import BytesIO
import tarfile
import os
import requests
from tests.base_case import ChatBotTestCase
from chatterbot.trainers import UbuntuCorpusTrainer


class UbuntuCorpusTrainerTestCase(ChatBotTestCase):
    """
    Test the Ubuntu Corpus trainer class.
    """

    def setUp(self):
        super().setUp()
        self.trainer = UbuntuCorpusTrainer(
            self.chatbot,
            ubuntu_corpus_data_directory='./.ubuntu_test_data/',
            show_training_progress=False
        )

        # Fake download url
        self.data_download_url = 'https://docs.chatterbot.us/ubuntu_dialogs.tgz'

    def tearDown(self):
        super().tearDown()

        self._remove_data()

    def _get_data(self):

        data1 = (
            b'2004-11-04T16:49:00.000Z	tom	jane	Hello\n'
            b'2004-11-04T16:49:00.000Z	tom	jane	Is anyone there?\n'
            b'2004-11-04T16:49:00.000Z	jane		Yes\n'
            b'\n'
        )

        data2 = (
            b'2004-11-04T16:49:00.000Z	tom	jane	Hello\n'
            b'2004-11-04T16:49:00.000Z	tom		Is anyone there?\n'
            b'2004-11-04T16:49:00.000Z	jane		Yes\n'
            b'\n'
        )

        return data1, data2

    def _remove_data(self):
        """
        Clean up by removing the corpus data directory.
        """
        import shutil

        if os.path.exists(self.trainer.data_directory):
            shutil.rmtree(self.trainer.data_directory)

    def _create_test_corpus(self, data):
        """
        Create a small tar in a similar format to the
        Ubuntu corpus file in memory for testing.
        """
        file_path = os.path.join(self.trainer.data_directory, 'ubuntu_dialogs.tgz')
        os.makedirs(self.trainer.data_directory, exist_ok=True)
        tar = tarfile.TarFile(file_path, 'a')

        tsv1 = BytesIO(data[0])
        tsv2 = BytesIO(data[1])

        tarinfo = tarfile.TarInfo('dialogs/3/1.tsv')
        tarinfo.size = len(data[0])
        tar.addfile(tarinfo, fileobj=tsv1)

        tarinfo = tarfile.TarInfo('dialogs/3/2.tsv')
        tarinfo.size = len(data[1])
        tar.addfile(tarinfo, fileobj=tsv2)

        tsv1.close()
        tsv2.close()
        tar.close()

        return file_path

    def _destroy_test_corpus(self):
        """
        Remove the test corpus file.
        """
        file_path = os.path.join(self.trainer.data_directory, 'ubuntu_dialogs.tgz')

        if os.path.exists(file_path):
            os.remove(file_path)

    def _mock_get_response(self, *args, **kwargs):
        """
        Return a requests.Response object.
        """
        response = requests.Response()
        response._content = b'Some response content'
        response.headers['content-length'] = len(response.content)
        return response

    def test_download(self):
        """
        Test the download function for the Ubuntu corpus trainer.
        """
        requests.get = Mock(side_effect=self._mock_get_response)
        download_url = 'https://example.com/download.tgz'
        self.trainer.download(download_url, show_status=False)

        file_name = download_url.split('/')[-1]
        downloaded_file_path = os.path.join(self.trainer.data_directory, file_name)

        requests.get.assert_called_with(download_url, stream=True)
        self.assertTrue(os.path.exists(downloaded_file_path))

        # Remove the dummy download_url
        os.remove(downloaded_file_path)

    def test_download_file_exists(self):
        """
        Test the case that the corpus file exists.
        """
        file_path = os.path.join(self.trainer.data_directory, 'download.tgz')
        os.makedirs(self.trainer.data_directory, exist_ok=True)
        open(file_path, 'a').close()

        requests.get = Mock(side_effect=self._mock_get_response)
        download_url = 'https://example.com/download.tgz'
        self.trainer.download(download_url, show_status=False)

        # Remove the dummy download_url
        os.remove(file_path)

        self.assertFalse(requests.get.called)

    def test_download_url_not_found(self):
        """
        Test the case that the url being downloaded does not exist.
        """
        self.skipTest('This test needs to be created.')

    def test_extract(self):
        """
        Test the extraction of text from a decompressed Ubuntu Corpus file.
        """
        file_object_path = self._create_test_corpus(self._get_data())
        self.trainer.extract(file_object_path)

        self._destroy_test_corpus()
        corpus_path = os.path.join(self.trainer.data_path, 'dialogs', '3')

        self.assertTrue(os.path.exists(self.trainer.data_path))
        self.assertTrue(os.path.exists(os.path.join(corpus_path, '1.tsv')))
        self.assertTrue(os.path.exists(os.path.join(corpus_path, '2.tsv')))

    def test_train(self):
        """
        Test that the chat bot is trained using data from the Ubuntu Corpus.
        """
        self._create_test_corpus(self._get_data())

        self.trainer.train(self.data_download_url, limit=50)
        self._destroy_test_corpus()

        response = self.chatbot.get_response('Is anyone there?')
        self.assertEqual(response.text, 'Yes')

    def test_train_sets_search_text(self):
        """
        Test that the chat bot is trained using data from the Ubuntu Corpus.
        """
        self._create_test_corpus(self._get_data())

        self.trainer.train(self.data_download_url, limit=50)
        self._destroy_test_corpus()

        results = list(self.chatbot.storage.filter(text='Is anyone there?'))

        self.assertEqual(len(results), 2, msg='Results: {}'.format(results))
        self.assertEqual(results[0].search_text, 'AUX:anyone PRON:there')

    def test_train_sets_search_in_response_to(self):
        """
        Test that the chat bot is trained using data from the Ubuntu Corpus.
        """
        self._create_test_corpus(self._get_data())

        self.trainer.train(self.data_download_url, limit=50)
        self._destroy_test_corpus()

        results = list(self.chatbot.storage.filter(in_response_to='Is anyone there?'))

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].search_in_response_to, 'AUX:anyone PRON:there')

    def test_is_extracted(self):
        """
        Test that a check can be done for if the corpus has aleady been extracted.
        """
        file_object_path = self._create_test_corpus(self._get_data())
        self.trainer.extract(file_object_path)

        extracted = self.trainer.is_extracted(self.trainer.data_path)
        self._destroy_test_corpus()

        self.assertTrue(extracted)

    def test_is_not_extracted(self):
        """
        Test that a check can be done for if the corpus has aleady been extracted.
        """
        self._remove_data()
        extracted = self.trainer.is_extracted(self.trainer.data_path)

        self.assertFalse(extracted)
