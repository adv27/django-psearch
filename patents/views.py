import os
import time

from django.core.paginator import Paginator
from django.http import (Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse)
from django.shortcuts import (redirect, render, reverse)
from django.views.generic.edit import FormView

from .forms import FileFieldForm
from .utils import *

SORT_BY_MAPPING = {
    '0': '$text_score',
    '1': '-rate',
    '2': '-view',
}

SEARCH_FIELD_MAPPING = {
    '0': 'all_fields',
    '1': 'title',
    '2': 'abstract',
    '3': 'content',
}


# Create your views here.

def index(request):
    context = {

    }
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


def search(request):
    t0 = time.time()
    query = request.GET.get('q')
    if query is not None:
        if query is not '':
            search_field = request.GET.get('field')
            if search_field is None or search_field == '' or search_field == '0':
                patent_list = Patent.objects.search_text(query)
            elif search_field in SEARCH_FIELD_MAPPING:
                if search_field == '1':
                    # title
                    patent_list = Patent.objects(title__icontains=query)
                if search_field == '1':
                    # abstract
                    patent_list = Patent.objects(abstract__icontains=query)
                if search_field == '1':
                    # title
                    patent_list = Patent.objects(content__icontains=query)
        else:
            patent_list = Patent.objects.all()

        # sort
        order_by = request.GET.get('ord')
        if order_by is None or order_by == '':
            patent_list.order_by('$text_score')
        elif order_by in SORT_BY_MAPPING:
            patent_list.order_by(SORT_BY_MAPPING.get(order_by))

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
    else:
        return redirect('/search?q={query}'.format(query=''))

    page_no = int(request.GET.get('page', 1))
    paginator = Paginator(patent_list, 10)  # Show 10 patents per page
    patents = paginator.get_page(page_no)

    '''
    we assume that if there are more than 11 pages 
    (current, 5 before, 5 after) we are always going to show 11 links. 
    Now we have 4 cases:
        Number of pages < 11: show all pages;
        Current page <= 6: show first 11 pages;
        Current page > 6 and < (number of pages - 6): show current page, 5 before and 5 after;
        Current page >= (number of pages -6): show the last 11 pages.
    '''
    num_pages = paginator.num_pages

    if num_pages <= 11 or page_no <= 6:  # case 1 and 2
        pages = [x for x in range(1, min(num_pages + 1, 12))]
    elif page_no > num_pages - 6:  # case 4
        pages = [x for x in range(num_pages - 10, num_pages + 1)]
    else:  # case 3
        pages = [x for x in range(page_no - 5, page_no + 6)]

    context = {
        'patents': patents,
        'pages': pages,
        'time': time.time() - t0,
        'query': query,
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

            'modify View Document'
            # if request has 'ref' param => the request come from search page
            # 'ref' param = search keyword
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
    from collections import Counter
    rates = Rate.objects.filter(patent_id=p)
    c = Counter(list(map(lambda _r: _r.rating, rates)))
    rate_count = dict(c)

    # Get average rate of this patent
    rate_avg = p.rate

    rate_titles = ['bad', 'poor', 'regular', 'good', 'gorgeous']

    context = {
        'patent': p,
        'time': time_query,
        'user_rating': r.rating if r is not None else None,
        'rate_titles': rate_titles,
        'rate_count': rate_count,
        'rate_avg': rate_avg,
    }

    return render(request, template_name='patents/show.html', context=context)


def login(request):
    if request.method == 'POST':
        u = User.objects(user_name__iexact=request.POST['username']).first()
        print(u.password)
        if u.password == request.POST['password']:
            request.session['user_id'] = str(u.id)
            return HttpResponseRedirect(reverse('patents:index'))
    return HttpResponseBadRequest()


def logout(request):
    try:
        del request.session['user_id']
    except KeyError:
        pass
    return HttpResponseRedirect(reverse('patents:index'))


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


def change_password_account(request):
    '''
    - Checking session to make sure that user have been logged in
    '''
    if request.method == 'POST':
        uid = request.session.get('user_id', False)
        if uid:
            u = User.objects.get(id=uid)
            new_password = request.POST.get('new_password')
            if new_password is None or new_password == '':
                return JsonResponse({
                    'error': True,
                    'message': 'New Password is invalid',
                })
            u.password = new_password
            u.save()
            return redirect(reverse('patents:index'))
        else:
            return JsonResponse({
                'error': True,
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

            'filter the files list, if the file name already in the db, then skip it'
            files = (f for f in files if Patent.objects.filter(filename=f.name).first() is None)
            with Pool(processes=15) as pool:  # using 15 processes to handle uploaded files
                file_list = ((f.name, f.read()) for f in files)
                pool.map(handle_uploaded_file_unpack, file_list)
                # pool.map(a_handle_uploaded_file, files)
                pool.close()
                pool.join()
            print('{}'.format(time.time() - t0))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
