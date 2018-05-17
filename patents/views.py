import time

from django.core.paginator import Paginator
from django.http import (Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse)
from django.shortcuts import (redirect, render, reverse)
from django.views.generic.edit import FormView

from .forms import FileFieldForm
from .utils import *


# Create your views here.

def index(request):
    context = {

    }
    return render(request, template_name='patents/index.html', context=context)


def search(request):
    t0 = time.time()
    query = request.GET.get('q')
    if query is not None:
        if query is not '':
            patent_list = Patent.objects.search_text(query).order_by('$text_score')
        else:
            patent_list = Patent.objects.all()

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

    page = request.GET.get('page', 1)
    paginator = Paginator(patent_list, 10)  # Show 10 patents per page
    patents = paginator.get_page(page)

    context = {
        'patents': patents,
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
                    print('Detail function: Wrong ref: {ref}, user: {user} don\'t make this search'.format(ref=ref,
                                                                                                           user=u.user_name))

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


def change_password_account(request):
    if request.method == 'POST':
        pass
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
            with Pool(processes=15) as pool:  # using 5 processes to handle uploaded files
                file_list = ((f.name, f.read()) for f in files)
                pool.map(handle_uploaded_file_unpack, file_list)
                pool.close()
                pool.join()
            print('{}'.format(time.time() - t0))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
