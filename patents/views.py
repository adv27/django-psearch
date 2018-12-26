import math
import pickle
import re
import time
import urllib.parse as urlparse

from django import forms
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect, JsonResponse)
from django.shortcuts import redirect, render, reverse
from django.views.decorators.csrf import csrf_protect
from django.views.generic.edit import FormView
from pymongo import DESCENDING

from recommend.recommend import Predict
from .search import search_patent
from .utils import *

SEARCH_FIELDS = {
    '1': 'Title',
    '2': 'Abstract',
    '3': 'Content',
}

SEARCH_FIELD_MAPPING = {
    '1': 'title',
    '2': 'abstract',
    '3': 'content',
}

SORT_BY_FIELDS = {
    0: 'Highest Text Score',
    1: 'Highest Rate',
    2: 'Highest View',
}

SORT_BY_MAPPING = {
    '0': '$text_score',
    '1': '-rate',
    '2': '-view',
}

# try to load LDA models here
time_load_start = time.time()
predict = Predict(num_of_rec=settings.NUMBER_OF_RECOMMENDATION)
path_doc_topic_matrix = './LDAmodel/doc_topic_matrix.pickle'
mappingFile = open(path_doc_topic_matrix, 'rb')
doc_topic_matrix = pickle.load(mappingFile)
mappingFile.close()
time_load_end = time.time()
model_load_time = time_load_end - time_load_start
print('Model load time: {}'.format(model_load_time))


# Create your views here.


def index(request):
    context = {}

    return render(request, template_name='patents/index.html', context=context)


def download(request, pat_id):
    try:
        p = Patent.objects.get(id=pat_id)
        filename = p.filename
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='text/xml')
                response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(file_path))
                return response
        raise Http404()
    except DoesNotExist:
        return JsonResponse({
            'error': True,
            'message': 'File not exits'
        })


def search_api(request):
    query = request.GET.get('q')
    fil = {}

    if query is None:
        return redirect('/search?q={query}'.format(query=''))

    page_no = int(request.GET.get('page', 1))
    start = (page_no - 1) * settings.ITEMS_PER_PAGE

    # get sort option
    order_by = request.GET.get('ord')
    sort_option = None
    if order_by is not None and order_by != '':
        sort_option = SORT_BY_MAPPING.get(order_by, None)

    if query is not '':
        search_field = request.GET.get('field')
        if search_field in SEARCH_FIELD_MAPPING:
            search_field_verbose = SEARCH_FIELD_MAPPING[search_field]
            regx = re.compile('.*{}.*'.format(query), re.IGNORECASE)
            f1 = {search_field_verbose: regx} if search_field_verbose != 'all_fields' else None
            f2 = {"$text": {"$search": query}}

            if f1 is not None:
                fil = {'$and': [f1, f2]}
            else:
                fil = f2

    # patents = search_patent(fil=fil, order_by=sort_option, skip=start, limit=settings.ITEMS_PER_PAGE)
    patents, count, search_time = search_patent(fil=fil, skip=start, limit=settings.ITEMS_PER_PAGE, time_search=True)

    return JsonResponse({
        'search_time': search_time,
        'count': count,
        'patents': patents
    })


def search(request):
    query = request.GET.get('q')
    patent_list = None

    if query is None:
        return redirect('/search?q={query}'.format(query=''))

    '''Just as with traditional ORMs, you may limit the number of results returned or skip a number or results in you query. limit() and skip() and methods are available on QuerySet objects, but the array-slicing syntax is preferred for achieving this.
    http://docs.mongoengine.org/guide/querying.html#limiting-and-skipping-results
    '''
    page_no = int(request.GET.get('page', 1))
    start = (page_no - 1) * settings.ITEMS_PER_PAGE
    end = start + settings.ITEMS_PER_PAGE

    # get sort option
    order_by = request.GET.get('ord')
    sort_option = None
    if order_by is not None and order_by != '':
        sort_option = SORT_BY_MAPPING.get(order_by, None)

    # get search field
    search_field = request.GET.get('field')

    time_query_start = time.time()

    patents = []
    count = None
    if (query is not '' and search_field == '3') or search_field is None:
        '''If user search patent by content
        Use pymongo to handle text search
        '''
        fil = {"$text": {"$search": query}}
        sort = None
        if sort_option == '$text_score':
            fil = [fil, {'score': {'$meta': 'textScore'}}]
            sort = [('score', {'$meta': 'textScore'})]
        elif sort_option is not None:
            sort = [(sort_option.strip('-'), DESCENDING)]
        patents, count = search_patent(
            fil=fil, skip=start, sort=sort, limit=settings.ITEMS_PER_PAGE
        )
        num_pages = math.ceil(count / settings.ITEMS_PER_PAGE)
    else:
        if query is not '':
            field = SEARCH_FIELD_MAPPING[search_field]
            sss = {'{field}__icontains'.format(field=field): query}
            if sort_option is not None:
                patent_list = Patent.objects(**sss).order_by(sort_option)
            else:
                patent_list = Patent.objects(**sss)
            count = patent_list.count()
            patent_list = patent_list[start:end]
        elif query is '':
            # User query empty (search nothing) then display all
            if sort_option is not None:
                patent_list = Patent.objects.order_by(sort_option)[start: end]
            else:
                patent_list = Patent.objects[start: end]
            count = Patent.objects.count()
        num_pages = math.ceil(count / settings.ITEMS_PER_PAGE)
        for p in patent_list:
            patents.append(p)

    # calculate time taken to query, sort and paginate
    time_query_end = time.time()
    time_query = time_query_end - time_query_start

    '''If user already logged in, change the query time of user
    and update Search Document.
    '''
    if request.session.get('user_id', False):
        uid = request.session.get('user_id')
        'modify user document'
        u = User.objects.get(id=uid)
        # increase query_count
        u.query_count += 1
        # modify user first_query, last_query
        u.query_last = datetime.now()
        if u.query_first is None:
            u.query_first = datetime.now()
        u.save()  # save the change

        'modify search document'
        try:
            s = Search.objects.get(
                user_id=u,
                keyword=query,
            )
            s.date = datetime.now()
        except DoesNotExist:
            s = Search(
                user_id=u,
                keyword=query,
                date=datetime.now(),
            )
        s.save()

    pages = get_paginate(page_no, num_pages)

    parsed = urlparse.urlparse(request.build_absolute_uri())
    queries_dict = urlparse.parse_qs(parsed.query, keep_blank_values=True)

    context = {
        'search_fields': SEARCH_FIELDS,
        'sort_fields': SORT_BY_FIELDS,
        'patents': patents,
        'time': time_query,
        'queries_dict': queries_dict,
        'query': query,
        'pages': pages,
        'total_pages': num_pages,
        'current_page': page_no,
    }

    return render(request, template_name='patents/listing.html', context=context)


def detail(request, pat_id):
    t0 = time.time()
    try:
        p = Patent.objects.get(id=pat_id)
    except (DoesNotExist, ValidationError) as e:
        print(e)
        raise Http404
    time_query = time.time() - t0
    # Increase view times
    p.view += 1
    p.save()

    # Checking if user is logged in
    # If user is logged in => get user's rate for this patent
    u = None
    r = None
    try:
        uid = request.session.get('user_id', False)
        if uid:
            u = User.objects.get(id=uid)
            try:
                r = Rate.objects.get(
                    user_id=u,
                    patent_id=p,
                )
            except DoesNotExist:
                r = None

            '''Adding this patent to user views'''
            if p not in u.views:
                u.views.append(p)
                u.save()

            '''
            Modify View Document
            If request has 'ref' param => the request come from search page
            'ref' param = search keyword
            '''
            ref = request.GET.get('ref')
            if ref is not None:
                try:
                    s = Search.objects.get(
                        user_id=u,
                        keyword=ref,
                    )
                    try:
                        v = View.objects.get(
                            search_id=s,
                            patent_id=p,
                        )
                        v.date = datetime.now()
                    except DoesNotExist:
                        v = View(
                            search_id=s,
                            patent_id=p,
                            date=datetime.now(),
                        )
                    v.save()
                except DoesNotExist:
                    print('Detail function: Wrong ref: {ref}, user: {user} don\'t make this search'.format(
                        ref=ref,
                        user=u.user_name)
                    )
    except DoesNotExist:
        pass

    # Get rates related to this patent
    rates = Rate.objects.filter(patent_id=p)
    rate_count = get_rate_percentage(rates=rates)

    # Get average rate of this patent
    rate_avg = p.rate

    rate_titles = ['bad', 'poor', 'regular', 'good', 'gorgeous']

    '''
    Get recommendation
    If (USE_USER_HISTORY) is True then use latest (N_RECENTLY_VIEWED) viewed patent 
    to generate user_dict
    '''
    user_dict = {}
    if settings.USE_USER_HISTORY and u:
        args = list(map(lambda p: str(p.pk), u.views[-settings.N_RECENTLY_VIEWED:]))
        # print(args)
    else:
        args = [pat_id]
    for arg in args:
        user_dict[arg] = doc_topic_matrix[arg]
    rec_ids = predict.run(user_dict, False)
    rec_patents = []
    for patent_id in rec_ids:
        pat = Patent.objects.get(id=patent_id)
        rec_patents.append(pat)

    context = {
        'search_fields': SEARCH_FIELDS,
        'patent': p,
        'time': time_query,
    }

    context.update({
        'user_rating': r.rating if r is not None else None,
        'rate_titles': rate_titles,
        'rate_count': rate_count,
        'rate_avg': rate_avg,
    })

    context.update({
        'rec_patents': rec_patents,
    })

    return render(request, template_name='patents/show.html', context=context)


@csrf_protect
def login(request):
    if request.method == 'POST':
        u = User.objects(user_name__iexact=request.POST['username']).first()
        if u is not None:
            if u.password == request.POST['password']:
                request.session['user_id'] = str(u.id)
                # return HttpResponseRedirect(reverse('patents:index'))
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                })
        return JsonResponse({
            'success': False,
            'message': 'Wrong credential',
        })
    return HttpResponseBadRequest()


def logout(request):
    try:
        del request.session['user_id']
    except KeyError:
        pass
    return HttpResponseRedirect(reverse('patents:index'))


@csrf_protect
def create_account(request):
    if request.method == 'POST':
        psw = request.POST.get('psw')
        psw_confirmation = request.POST.get('psw_confirmation')
        name = request.POST.get('u')
        if psw != psw_confirmation:
            return JsonResponse({
                'success': False,
                'message': 'Password confirmation not matchl'
            })
        if create_user_validation(username=name, password=psw):
            create_user(username=name, password=psw)
            return JsonResponse({
                'success': True,
                'message': 'Account create successful'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Validation failed'
            })
    return HttpResponseBadRequest()


def change_password_account(request):
    """
    - Checking session to make sure that user have been logged in
    """
    if request.method == 'POST':
        uid = request.session.get('user_id', False)
        if uid:
            u = User.objects.get(id=uid)
            if u:
                current_password = request.POST.get('current_psw')
                if current_password != u.password:
                    return JsonResponse({
                        'success': False,
                        'message': 'Current password not match',
                    })

                new_password = request.POST.get('new_psw')
                new_password_confirmation = request.POST.get('new_psw_confirmation')
                if new_password is None or new_password == '':
                    return JsonResponse({
                        'success': False,
                        'message': 'New Password is invalid',
                    })
                if new_password != new_password_confirmation:
                    return JsonResponse({
                        'success': False,
                        'message': 'Password confirmation not match',
                    })

                u.password = new_password
                u.save()
                # return redirect(reverse('patents:index'))
                logout(request)
                return JsonResponse({
                    'success': True,
                    'message': 'Password changed',
                })
        return JsonResponse({
            'success': False,
            'message': 'Permission denied',
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
            u = User.objects.get(id=uid)
            p = Patent.objects.get(id=patent_id)
            try:
                r = Rate.objects.get(
                    user_id=u,
                    patent_id=p,
                )
                # if rate is matching in the db, update it's rating and date
                r.rating = rating
                r.date = datetime.now()
            except DoesNotExist:
                # create new rate document
                r = Rate(
                    user_id=u,
                    patent_id=p,
                    rating=rating,
                    date=datetime.now()
                )
            if r is not None:
                # save it
                r.save()
                # re-calculate average rate from Patent Document then save it
                rates = Rate.objects.filter(patent_id=p)
                from statistics import mean
                p.rate = mean(list(map(lambda _r: _r.rating, rates)))
                p.save()

                from .templatetags.app_filters import rate_times
                rate_times = rate_times(p)

                rate_count = get_rate_percentage(rates)

                jsonRes = JsonResponse({
                    'uid': str(r.user_id.id),
                    'pid': str(r.patent_id.id),
                    'rating': r.rating,
                    'rate_avg': p.rate,
                    'date': r.date,
                    'rate_times': rate_times,
                    'rate_count': rate_count,
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


class UploadFileForm(forms.Form):
    file_field = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))
    directory_field = forms.CharField(required=False, help_text='Directory contains xml files')


class FileFieldView(FormView):
    form_class = UploadFileForm
    template_name = 'patents/upload.html'
    # success_url = reverse('patents:upload')
    success_url = '../upload'

    def post(self, request, *args, **kwargs):
        from multiprocessing import Pool

        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files_field = request.FILES.getlist('file_field')
        directory_field = request.POST.get('directory_field')
        if form.is_valid():
            t0 = time.time()
            if directory_field:
                if os.path.exists(directory_field):
                    print(directory_field)
                    file_names = os.listdir(directory_field)
                    'filter the file name list, only take .xml file'
                    file_names = list(filter(lambda name: os.path.splitext(name.lower())[1] == '.xml', file_names))
                    'if the file name already in the db, then skip it'
                    f_in = Patent.objects(filename__in=file_names)
                    f_in = list(map(lambda d: d['filename'], f_in))
                    file_names = list(set(file_names) - set(f_in))

                    # 'join the file name with the directory path, to get the file path on computer'
                    file_paths = map(lambda name: os.path.join(directory_field, name), file_names)

                    with Pool(processes=15) as pool:
                        pool.map(handle_uploaded_path, file_paths)
                        pool.close()
                        pool.join()
                else:
                    print("directory doesn't exist")
            elif files_field:
                print('len(files): {}, type: {}'.format(len(files_field), type(files_field)))
                'filter the files list, if the file name already in the db, then skip it'
                files = (f for f in files_field if Patent.objects.filter(filename=f.name).first() is None)
                with Pool(processes=15) as pool:  # using 15 processes to handle uploaded files
                    file_list = ((f.name, f.read()) for f in files)
                    pool.map(handle_uploaded_file_unpack, file_list)
                    pool.close()
                    pool.join()
            print('{}'.format(time.time() - t0))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
