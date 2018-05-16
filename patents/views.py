import time

from django.core.paginator import Paginator
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import (
    render,
    reverse,
)
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
        if request.session.get('user_id', False):
            uid = request.session.get('user_id')
            u = User.objects.get(id=uid)
            # increase query_count
            u.query_count += 1
            # modify user first_query, last_query
            u.query_last = datetime.now()
            if u.query_first is None:
                u.query_first = datetime.now()
            u.save()  # save the change
    else:
        patent_list = Patent.objects.all()
    page = request.GET.get('page', 1)
    paginator = Paginator(patent_list, 10)  # Show 10 patents per page
    patents = paginator.get_page(page)

    context = {
        'patents': patents,
        'time': time.time() - t0,
    }

    return render(request, template_name='patents/listing.html', context=context)


def detail(request, pat_id):
    t0 = time.time()

    r = None
    try:
        uid = request.session.get('user_id', False)
        if uid:
            r = Rate.objects.get(
                user_id=User.objects.get(id=uid),
                patent_id=Patent.objects.get(id=pat_id),
            )
    except DoesNotExist:
        pass

    rate_titles = ['bad', 'poor', 'regular', 'good', 'gorgeous']

    context = {
        'patent': Patent.objects.get(id=pat_id),
        'time': time.time() - t0,
        'rating': r.rating if r is not None else None,
        'rate_titles': rate_titles,
    }

    return render(request, template_name='patents/show.html', context=context)


def login(request):
    if request.method == 'POST':
        u = User.objects(user_name__iexact=request.POST['username']).first()
        print(u.password)
        if u.password == request.POST['password']:
            request.session['user_id'] = str(u.id)
            return HttpResponseRedirect(reverse('patents:search'))
    return HttpResponseBadRequest()


def logout(request):
    try:
        del request.session['user_id']
    except KeyError:
        pass
    return HttpResponseRedirect(reverse('patents:search'))


def create_account(request):
    if request.method == 'POST':
        pwd = request.POST.get('password')
        name = request.POST.get('username')
        if create_user_validation(username=name, password=pwd):
            create_user(username=name, password=pwd)
            return JsonResponse({
                'success': True,
                'error': True,
                'message': 'Account create successful'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': True,
                'message': 'Validation failed'
            })
    return HttpResponseBadRequest()


def rate(request):
    patent_id = None
    rating = int()
    if request.method == 'GET':
        patent_id = request.GET.get('pid', False)
        rating = request.GET.get('rating', False)
    elif request.method == 'POST':
        patent_id = request.POST.get('pid', False)
        rating = request.POST.get('rating', False)
    if patent_id and rating:
        # checking user session
        uid = request.session.get('user_id', False)
        if uid:
            try:
                r = Rate.objects.get(
                    user_id=User.objects.get(id=uid),
                    patent_id=Patent.objects.get(id=patent_id),
                )
                r.rating = rating
                r.save()
            except DoesNotExist:
                r = Rate(
                    user_id=User.objects.get(id=uid),
                    patent_id=Patent.objects.get(id=patent_id),
                    rating=rating,
                    date=datetime.now()
                )
                r.save()
            if r is not None:
                jsonRes = JsonResponse({
                    'uid': str(r.user_id.id),
                    'pid': str(r.patent_id.id),
                    'rating': r.rating,
                    'date': r.date
                })
                return jsonRes
            else:
                return JsonResponse({
                    'error': True
                })
        else:
            return HttpResponse('uid false')
    else:
        return HttpResponse('patent and rating false')


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
