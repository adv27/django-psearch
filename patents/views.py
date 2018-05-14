import time

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic.edit import FormView

from .forms import FileFieldForm
from .models import *
from .utils import *

# Create your views here.

def index(request):
    pass


def search(request):
    t0 = time.time()
    query = request.GET.get('q')
    if query:
        patent_list = Patent.objects.search_text(query).order_by('$text_score')
    else:
        patent_list = Patent.objects.all()
    page = request.GET.get('page', 1)
    paginator = Paginator(patent_list, 10)  # Show 10 patents per page
    patents = paginator.get_page(page)

    context = {
        'pattens': patents,
        'time': time.time() - t0,
    }

    render(request, template_name='search.html', context=context)


def show(request, pat_id):
    t0 = time.time()
    context = {
        'patent': Patent.objects.filter(id=pat_id).first(),
        'time': time.time() - t0,
    }

    render(request, template_name='show.html', context=context)


class FileFieldView(FormView):
    form_class = FileFieldForm
    template_name = 'patents/upload.html'
    # success_url = reverse('patents:upload')
    success_url = '../upload'

    def post(self, request, *args, **kwargs):

        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            t0 = time.time()
            print('len(files): {}, type: {}'.format(len(files), type(files)))
            # for f in files:
            #     filename = basename(f.name)
            #     print(filename)
            #     _dict = xmltodict.parse(f)
            #     _json = json.dumps(_dict)
            #     doc = json.loads(_json)
            #     save_mongo(filename=filename, doc=doc)

            # with Pool(processes=5) as pool:
            #     file_list = ((f.name,f.read()) for f in files)
            #     pool.map(self.handle_uploaded_file, file_list)
            #     # pool.map(self.handle_uploaded_file, files)
            #     pool.close()
            #     pool.join()
            #     # if Patent.objects.filter(filename=filename).first():

            for i in ((f.name, f.read()) for f in files):
                print('{name} - {sample_data}'.format(name=i[0], sample_data=i[1][:20]))
                save_mongo(*i)
            print('{}'.format(time.time() - t0))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    @staticmethod
    def handle_uploaded_file(filestream, filename):
        import xmltodict
        import json

        _dict = xmltodict.parse(filestream)
        _json = json.dumps(_dict)
        doc = json.loads(_json)
        save_mongo(filename=filename, doc=doc)
