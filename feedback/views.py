from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import UpdateView, ListView
from .forms import NameForm
from django.contrib.auth.admin import User
from .models import Form as MyForm
from .models import Question as MyQuestion
from .models import Answer as MyAnswer
from .models import response_user_list as Myresp
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.admin import User as Myuser
from django.utils.decorators import method_decorator
from django.views.generic import View
from .models import response_user as rf
from django.contrib.auth.decorators import login_required
import re
import copy


class LoginRequired(View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequired, self).dispatch(*args, **kwargs)


# class IndexListView(LoginRequired, ListView):
#     model = MyForm
#     template_name = 'feedback/index.html'
#     context_object_name = 'userform'
#     paginate_by = 2
#
#     # ordering = ['-form_posted']
#
#     def get_queryset(self):
#         return MyForm.objects.filter(user=self.request.user)
#


def delete_question(request):
    if request.user.is_authenticated:
        qid = request.POST.get("qid", "")
        if qid != "":
            q = MyQuestion.objects.filter(pk=qid)[0]
            if q:
                q.delete()
                message = "Deleted Successfully"
            else:
                message = "Not Able To Delete"
        else:
            message = "Not Such Question"
    else:
        message = "Unauthorised Access"
    return render(request, "feedback/message.html", {"message": message})

def updatequestion(request):
    if request.method == "GET":
        qid = request.GET.get("qid","")
        if qid == "":
            return redirect("/users/")


        if not request.user.is_authenticated:
            return redirect("/users/")

        user = request.user
        question = MyQuestion.objects.filter(pk=qid)[0]

        form = MyForm.objects.filter(question=question)[0]
    #    print(form.user)
   #     print(user)

        if form.user != user:
        #    print("ret")
            return redirect("/users/")
        else:
            ques_text = question.ques_text
            type = question.ques_type
            optionlist = None
            if type == "chk" or type == "cho":
                regex = re.compile("([A-z_ -*+0-9]+).\(,\)")
                optionlist = regex.findall(question.ques_option)
            if type == "rg" or type=="tx":
                optionlist = question.ques_option
            formurl = "/feedback/question/delete/",question.id
            return render(request,"feedback/update_question.html",
                          {"ques_text":ques_text,
                           "optionlist":optionlist,
                           "type":type,
                           "qid":qid
                           })
    if request.method == "POST":
        qid = request.POST.get("qid","")
        if qid is None:
            return redirect("/feedback/")

        type = request.POST.get("type","")
        ques_text = ""
        quest_numb_option = 0
        if type == 'cho':
            option1 = request.POST.get("option1", "")
            option2 = request.POST.get("option2", "")
            option3 = request.POST.get("option3", "")
            option4 = request.POST.get("option4", "")

            if option1 != "":
                ques_text += option1 + " (,)"
                quest_numb_option += 1
            if option2 != "":
                ques_text += option2 + " (,)"
                quest_numb_option += 1
            if option3 != "":
                ques_text += option3 + " (,)"
                quest_numb_option += 1
            if option4 != "":
                ques_text += option4 + " (,)"
                quest_numb_option += 1
        elif type == 'chk':
            option1 = request.POST.get("option1", "")
            option2 = request.POST.get("option2", "")
            option3 = request.POST.get("option3", "")
            option4 = request.POST.get("option4", "")

            if option1 != "":
                ques_text += option1 + " (,)"
                quest_numb_option += 1
            if option2 != "":
                ques_text += option2 + " (,)"
                quest_numb_option += 1
            if option3 != "":
                ques_text += option3 + " (,)"
                quest_numb_option += 1
            if option4 != "":
                ques_text += option4 + " (,)"
                quest_numb_option += 1

        elif type == 'tx':
            mytextarea = request.POST.get("tx", "")
            ques_text = mytextarea
            quest_numb_option += 1
        elif type == 'rg':
            myrange = request.POST.get("range", "")
            ques_text = myrange
            quest_numb_option += 1
            regex = re.compile(r'^([0-9]+)$')
            if not regex.match(ques_text):
                userquestion = MyQuestion.objects.filter(pk=qid)[0]
                return render(request, "feedback/message.html", {"message": "Not valid Input", "next": "/feedback/form/about/"+str(userquestion.form.id)})


        userquestion = MyQuestion.objects.filter(pk=qid)[0]
        userquestion.quest_numb_option = quest_numb_option
        userquestion.ques_text = request.POST.get("ques_text", "")
        userquestion.ques_option = ques_text
        userquestion.save()
        return redirect("/feedback/form/about/"+str(userquestion.form.id))


def index(request):
    template_name = 'feedback/index.html'
    if request.user.id:
        #print(request.user.id)
        userform = MyForm.objects.filter(user=request.user)
        myrf = rf.objects.filter(user=request.user)
        #print("reform")
        #print(myrf)
        responseform = list()
        for myform in myrf:
            given = Myresp.objects.filter(user=request.user, form=myform.form)
            #print("given")
            #print(given)
            if not given.exists():
             #   print("append")
            #    print(myform)
                responseform.append(myform)
        return render(request, template_name, {'userform': userform , 'responseform':responseform})
    else:
        return render(request, template_name)


def createForm(request):
    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(pk=request.user.id)[0]
            myform = MyForm()
            myform.user = user
            myform.form_heading = form.cleaned_data["form_heading"]
            myform.form_status = form.cleaned_data["form_status"]
            myform.save()

        # return render(request, 'users/index.html', {'myform': myform})
        return redirect("/feedback/")

    else:
        form = NameForm()

    return render(request, 'feedback/form.html', {'form': form})


def displayForm(request):
    if request.user.is_authenticated:
        q = MyQuestion()
        userform = MyForm.objects.filter(user=request.user)
        return render(request, "feedback/userform.html", {"userforms": userform})
    else:
        return redirect('users/login/')


def manage(request):
    if not request.user.is_authenticated:
        return redirect('users/login/')
    if request.POST.get("myaction", "") == "addquestion":
        return addQuestion(request)

    if request.GET.get("myaction", "") == "edit":
        return editForm(request)
    elif request.GET.get("myaction", "") == "share":
        return shareForm(request)
    elif request.GET.get("myaction", "") == "response":
        return viewResponse(request)
    elif request.GET.get("myaction", "") == "addquestion":
        return addQuestion(request)
    elif request.GET.get("myaction", "") == "remove":
        return removeForm(request)
    else:
        return shareEmail(request)
        # return render(request, "feedback/myaction.html",
        # {'myaction': request.GET.get("myaction", ""), 'id': request.GET.get("formid", "")})


def addQuestion(request):
    if request.method == "POST":

        ques_text = ""
        quest_numb_option = 0
        if request.POST.get("type", "") == 'cho':
            option1 = request.POST.get("option1", "")
            option2 = request.POST.get("option2", "")
            option3 = request.POST.get("option3", "")
            option4 = request.POST.get("option4", "")

            if option1 != "":
                ques_text += option1 + " (,)"
                quest_numb_option += 1
            if option2 != "":
                ques_text += option2 + " (,)"
                quest_numb_option += 1
            if option3 != "":
                ques_text += option3 + " (,)"
                quest_numb_option += 1
            if option4 != "":
                ques_text += option4 + " (,)"
                quest_numb_option += 1
        elif request.POST.get("type", "") == 'chk':
            option1 = request.POST.get("option1", "")
            option2 = request.POST.get("option2", "")
            option3 = request.POST.get("option3", "")
            option4 = request.POST.get("option4", "")

            if option1 != "":
                ques_text += option1 + " (,)"
                quest_numb_option += 1
            if option2 != "":
                ques_text += option2 + " (,)"
                quest_numb_option += 1
            if option3 != "":
                ques_text += option3 + " (,)"
                quest_numb_option += 1
            if option4 != "":
                ques_text += option4 + " (,)"
                quest_numb_option += 1

        elif request.POST.get("type", "") == 'tx':
            mytextarea = request.POST.get("mytextarea", "")
            ques_text = mytextarea
            quest_numb_option += 1
        elif request.POST.get("type", "") == 'rg':
            myrange = request.POST.get("myrange", "")
            ques_text = myrange
            quest_numb_option += 1
        # return render(request,
        #               "feedback/myaction.html",
        #               {
        #                   "id": request.POST.get("formid", ""),
        #                   "question_description": request.POST.get("question_description", ""),
        #                    "type": request.POST.get("type", ""),
        #                   # "option1": request.POST.get("option1", ""),
        #                   # "option2": request.POST.get("option2", ""),
        #                   # "option3": request.POST.get("option3", ""),
        #                   # "option4": request.POST.get("option4", ""),
        #                   # "mytextarea": request.POST.get("mytextarea", ""),
        #                   # "myrange": request.POST.get("myrange", ""),
        #                   "ques_text": ques_text,
        #               }
        #               )
        id = request.POST.get("formid", "")
        userform = MyForm.objects.filter(pk=id)[0]
        userquestion = MyQuestion()
        userquestion.form = userform
        userquestion.quest_numb_option = quest_numb_option
        userquestion.ques_text = request.POST.get("question_description", "")
        userquestion.ques_type = request.POST.get("type", "")
        userquestion.ques_option = ques_text
        if userquestion.ques_type == "rg":
            regex = re.compile(r'^([0-9]+)$')
            if not regex.match(userquestion.ques_option):
                return render(request, "feedback/message.html", {"message":"Not valid Input"})
            userquestion.ques_option = int(userquestion.ques_option)
        userquestion.save()
        #return render(request, 'users/index.html')
        return redirect("/feedback/")

    else:
        if request.GET.get("type", "") == "":
            type = "chk"
        else:
            type = request.GET.get("type", "")

        if request.GET.get("formid", "") == "":
            return render(request, 'feedback/index.html')
        else:
            formid = request.GET.get("formid", "")

        return render(request,
                      "feedback/question.html",
                      {'myaction': "add question",
                       'id': request.GET.get("formid", ""),
                       'type': type,
                       'formid': formid,
                       },
                      )


def editForm(request):
    return redirect('form/update/' + request.GET.get("formid", ""))


def shareForm(request):
    return render(request, "feedback/share.html", {'formid': request.GET.get("formid", "")})
    # return render(request, "feedback/myaction.html",{'myaction': "share", 'id': request.GET.get("formid", "")})


def viewResponse(request):
    return mychart(request)


def removeForm(request):
    userform = MyForm.objects.filter(pk=request.GET.get("formid", ""))[0].delete()
    return redirect('/feedback')


def aboutForm(request, formid):
    if not request.user.is_authenticated:
        return redirect('/users/login/')
    userform = MyForm.objects.filter(pk=formid)[0]
    questions = MyQuestion.objects.filter(form=userform)
    return render(request,
                  "feedback/form-about.html",
                  {"form": userform,
                   "questions": questions,
                   },
                  )


class UpdateForm(LoginRequired, UpdateView):
    model = MyForm
    template_name_suffix = '_update_form'
    # fields = ["form_heading", "form_status", "form_type"]
    fields = ["form_heading", "form_status"]


def IndividualFormAns(request, formid):
    if not request.user.is_authenticated:
        return redirect('users/login/')
    # select * from feedback_answer left join auth_user au on feedback_answer.user_id = au.id left join feedback_question fq on feedback_answer.question_id = fq.id;
    resp = Myresp.objects.filter(form_id=formid)
    userform = MyForm.objects.filter(pk=formid)
    name = Myuser.objects.raw(
        'select auth_user.id,username from auth_user left join feedback_response_user_list frul on auth_user.id = frul.user_id where form_id=%s',
        [formid])
    return render(request,
                  "feedback/individualresp.html",
                  {
                      "form": userform,
                      "resp": resp,
                      "name": name,
                      "form_id": formid

                  },
                  )


def UserResp(request):
    if not request.user.is_authenticated:
        return redirect('users/login/')
    userid = request.GET.get("userid")
    formid = request.GET.get("formid")
    userform = MyForm.objects.filter(pk=formid)[0]
    resp = MyAnswer.objects.raw(
        'select * from feedback_question left join feedback_answer fa on feedback_question.id = fa.question_id where user_id=%s and fa.form_id=%s',
        [userid, formid])

    return render(request, "feedback/userresp.html",
                  {
                      "form": userform,
                      "resp": resp
                  })


@login_required()
def formResponse(request, formid):
    userform = MyForm.objects.filter(pk=formid)[0]
    questions = MyQuestion.objects.filter(form_id=formid)
    userchk = Myresp.objects.filter(form_id=formid, user_id=request.user)
    given = MyAnswer.objects.filter(user=request.user,form_id=formid)
    if given:
        #html = "<html><body><h1>You already responded</h1></body></htmL>"
        #return HttpResponse(html)
        message = "You already responded"
        return render(request, "feedback/message.html", {"message":message})

    return render(request,
                      "response/form-answer.html",
                      {
                          "form": userform,
                          "questions": questions,
                      },
                      )


def subans(request):
    formid = request.POST.get("formid", "")
    questions = MyQuestion.objects.filter(form_id=formid)
    respform = Myresp()
    respform.user = request.user
    respform.form = MyForm.objects.filter(pk=formid)[0]
    respform.save()
    for q in questions:
        userans = MyAnswer()
        userans.form = MyForm.objects.filter(pk=formid)[0]
        userans.user = request.user
        userans.question = q;
        answer = ""
        regex = re.compile("([A-z_ -*+0-9]+).\(,\)")
        optionlist = regex.findall(q.ques_option)
        if q.ques_type == 'chk':
            for option in optionlist:
                param = str(q.id) + "-" + str(option)
                if request.POST.get(param, "") == option:
                    answer += str(option) + " (,)"
            userans.answer = answer
            userans.save()
        if q.ques_type == 'rg':
            param = str(q.id)
            answer = request.POST.get(param, "")
            userans.answer = answer
            userans.save()
        if q.ques_type == 'tx':
            param = str(q.id)
            answer = request.POST.get(param, "")
            userans.answer = answer
            userans.save()
        if q.ques_type == 'cho':
            param = str(q.id)
            answer = request.POST.get(param, "")
            userans.answer = answer
            userans.save()
    return redirect("/feedback/")


def mychart(request):
    if not request.user.is_authenticated:
        return redirect('/users/login/')
    if request.method == "GET":
        form_id = request.GET.get("formid", "")
        if form_id != "":
            my_data_struct = list()
            regex = re.compile("([A-z_ -*+0-9]+).\(,\)")

            questions = MyQuestion.objects.filter(form_id=form_id)

            bgColor = [
                'rgba(31, 153, 234, 1)',
                'rgba(229, 102, 221, 1)',
                'rgba(99, 217, 207, 1)',
                'rgba(226, 54, 60, 1)',
                'rgba(209, 108, 0, 1)',
                'rgba(93, 241, 30, 1)'
            ]
            bColor = [
                'rgba(10, 112, 255, 1)',
                'rgba(166, 28, 157, 1)',
                'rgba(42, 172, 162, 1)',
                'rgba(156, 22, 27, 1)',
                'rgba(138, 71, 0, 1)',
                'rgba(45, 129, 8, 1)'
            ]
            num_color = 6
            for q in questions:
                response_list = list()
                description = q.ques_text
                type = q.ques_type
                q_id = q.id
                graph = "row"
                backgroundColor = list()
                borderColor = list()
                #  print("Description :", description, " Type : ", type)
                if q.ques_type == "rg":
                    regex = re.compile(r'^([0-9]+)$')
                    if regex.match(q.ques_option):
                        label = list(range(1, int(q.ques_option) + 1))
                        data = [0] * int(q.ques_option)
                        graph = "bar"
                        answers = MyAnswer.objects.filter(question_id=q.id)

                        for i in range(int(q.ques_option)):
                            backgroundColor.append(bgColor[i % num_color])
                            borderColor.append(bColor[i % num_color])

                        # print("Answers : ", answers)
                        for a in answers:
                            index = int(a.answer) - 1
                            data[index] = data[index] + 1
                    else:
                        description = "Not Valid input For This Question"
                if q.ques_type == "chk":
                    label = list()
                    data = [0] * int(q.quest_numb_option)
                    graph = "bar"
                    option_list = regex.findall(q.ques_option)
                    for option in option_list:
                        label.append(option)
                    answers = MyAnswer.objects.filter(question_id=q.id)
                    for i in range(int(q.quest_numb_option)):
                        backgroundColor.append(bgColor[i % num_color])
                        borderColor.append(bColor[i % num_color])
                    # print("Answers : ", answers)
                    for a in answers:
                        answers_list = regex.findall(a.answer)
                        for each_answer in answers_list:
                            index = label.index(each_answer)
                            data[index] = data[index] + 1
                    # print("Data : ", data)

                if q.ques_type == "cho":
                    label = list()
                    data = [0] * int(q.quest_numb_option)
                    graph = "bar"
                    option_list = regex.findall(q.ques_option)
                    for option in option_list:
                        label.append(option)
                    answers = MyAnswer.objects.filter(question_id=q.id)
                    for i in range(int(q.quest_numb_option)):
                        backgroundColor.append(bgColor[i % num_color])
                        borderColor.append(bColor[i % num_color])
                    # print("Answers : ", answers)
                    for a in answers:
                        index = label.index(a.answer)
                        data[index] = data[index] + 1
                    # print("Data : ", data)

                if q.ques_type == "tx":
                    label = list()

                    data = MyAnswer.objects.filter(question_id=q.id)[:10]
                    graph = "row"

                response_list.append(q_id)  # 0
                response_list.append(type)  # 1
                response_list.append(description)  # 2
                response_list.append(data)  # 3
                response_list.append(label)  # 4
                response_list.append(graph)  # 5
                response_list.append(backgroundColor)  # 6
                response_list.append(borderColor)  # 7

                my_data_struct.append(response_list)

            return render(request, "feedback/response.html", {"my_data_struct": my_data_struct, "formid": form_id})
            # return render(request, "feedback/myaction.html", {"my_data_struct": my_data_struct, 'id': request.GET.get("formid", "")})


        else:
            redirect("/feedback/")
    else:
        redirect("/feedback/")


def shareEmail(request):
    if not request.user.is_authenticated:
        message = "Unauthorised Access"
        return render(request, "feedback/message.html", {"message": message, "next": "/users/login","success": ""})

    fid = request.GET.get("formid", None)
    emails = request.GET.get("email", None)
    if not emails:
        message = "No Email Given"
        return render(request, "feedback/message.html", {"message": message, "next": "/feedback/", "success": ""})

    feedback_link = "http://formvilla.herokuapp.com/feedback/formresp/" + fid
    lis = emails.split(",")
    notgiven = list()
    for i in range(0, len(lis)):
        lis[i] = lis[i].strip(' ')
     #   print(lis[i])
        usermy = Myuser.objects.filter(email=lis[i])
        if not usermy:
            notgiven.append(lis[i])
        else:
            usermy = Myuser.objects.filter(email=lis[i])[0]
        if usermy:
            respform = rf()
            respform.user = usermy
            respform.form = MyForm.objects.filter(pk=fid)[0]
            given = rf.objects.filter(user=usermy, form=respform.form)
            if not given:
               # print("given")
                respform.save()
                mail_body = " Your Feedback Can Be Recorded By Using : " + feedback_link
                send_mail('FEEDBACK FORM ', mail_body, settings.EMAIL_HOST_USER, [lis[i]], fail_silently=False)

    # SUCCESS MESSAGE AND FAILURE HANDLING IS LEFT
    if len(notgiven)>0:
        return render(request, "feedback/message.html", {"message": "List Of Email which doesn't Exist ","notgiven": notgiven, "next": "/feedback/", "success": ""})
    else:
        return render(request, "feedback/message.html", {"success": "Send Successfully", "next": "/feedback/"})
    #return redirect("/feedback")


def form_course(request):
    if not request.user.is_authenticated:
        return redirect("/users/login")
    mypk = 25
    myform = MyForm()
    form = MyForm.objects.filter(pk=mypk)[0]
    if not form:
        redirect("/feedback/")
    qlist =MyQuestion.objects.filter(form=form)
    myform.form_heading = form.form_heading
    myform.form_status = form.form_status
    myform.user = request.user
    myform.save()
    for question in qlist:
        q = MyQuestion()
        q.form = myform
        q.ques_text = question.ques_text
        q.ques_type = question.ques_type
        q.quest_numb_option = question.quest_numb_option
        q.ques_option = question.ques_option
        q.save()
    #print(form.id)
    #print(myform.id)
    return redirect("/feedback/")
