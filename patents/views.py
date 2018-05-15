import time

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic.edit import FormView

from .forms import FileFieldForm
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

    return render(request, template_name='patents/listing.html', context=context)


def show(request, pat_id):
    t0 = time.time()
    context = {
        'patent': Patent.objects.filter(id=pat_id).first(),
        'time': time.time() - t0,
    }

    return render(request, template_name='show.html', context=context)


class FileFieldView(FormView):
    form_class = FileFieldForm
    template_name = 'patents/upload.html'
    # success_url = reverse('patents:upload')
    success_url = '../upload'

    def post(self, request, *args, **kwargs):
        from multiprocessing import Pool

        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            t0 = time.time()
            print('len(files): {}, type: {}'.format(len(files), type(files)))
            # for f in files:
            #     print(f.name)
            #     _dict = xmltodict.parse(f)
            #     _json = json.dumps(_dict)
            #     doc = json.loads(_json)
            #     save_mongo(filename=f.name, doc=doc)

            'filter the files list'
            files = (f for f in files if Patent.objects.filter(filename=f.name).first() is None)
            with Pool(processes=15) as pool:  # using 5 processes to handle uploaded files
                file_list = ((f.name, f.read()) for f in files)
                pool.map(handle_uploaded_file_unpack, file_list)
                pool.close()
                pool.join()
            print('{}'.format(time.time() - t0))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
