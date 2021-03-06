from django.contrib import auth
from django.http import Http404
from rest_framework import generics, status, filters
import rest_framework
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_condition import Or
# from drf_composable_permissions.permissions import IsReadOnly, IsSuperuser
# from drf_composable_permissions.p import P

from main.models import *
from utils.calc import create_calc
from .serializers import *
import hashlib


class SubjectListView(generics.ListAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class RegisterView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                username = request.data.get('username')
                serializer.save()
                id = User.objects.get(username=username).id
                Profile.objects.create(user_id=id)

                return Response({
                    'status': 'succes',
                    'code': status.HTTP_200_OK,
                    'message': "Регистрация прошла успешно",
                    'data': {
                        'username': username,
                    },
                })

        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class UsernameCheckView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        username = request.data.get('username')
        checked = User.objects.filter(username=username).exists()

        if checked:
            return Response({
                'status': 400,
                'data': 'Имя пользователя не доступно',
            })

        return Response({
                'status': 200,
                'data': 'Доступно',
            })


class LoginView(APIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny, )

    @staticmethod
    def post(request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            user = auth.authenticate(username=username, password=password)

            if user is not None:
                token, created = Token.objects.get_or_create(user=user)

                return Response({
                    'token': token.key,
                    'username': username
                })
            else:
                return Response("Неверное имя пользователя или пароль", status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class MeView(APIView):
    permission_classes = (Or(IsAdminUser, IsAuthenticated),)

    @staticmethod
    def get(request):
        try:
            user = request.user
            point = user.profile.rating

            if 0 < point < 100:
                user.profile.status = 'новичок'
                user.profile.save()
            elif 100 <= point < 300:
                user.profile.status = 'середнячок'
                user.profile.save()
            elif 300 <= point < 500:
                user.profile.status = 'хорошист'
                user.profile.save()
            elif 500 <= point < 1000:
                user.profile.status = 'умный'
                user.profile.save()
            elif 1000 <= point < 3000:
                user.profile.status = 'отличник'
                user.profile.save()
            elif 3000 <= point < 5000:
                user.profile.status = 'ученый'
                user.profile.save()
            elif 5000 <= point < 8000:
                user.profile.status = 'почетный грамотей'
                user.profile.save()
            else:
                user.profile.status = 'профессор'
                user.profile.save()
            if user.profile.user_image:
                image = user.profile.user_image.url
            else:
                image = None
            return Response({
                'status': 200,
                'data': {
                    'user': {
                        'user_id': user.pk,
                        'username': user.username,
                        'date_joined': user.date_joined,
                        'rating': user.profile.rating,
                        'status': user.profile.status,
                        'image': image,
                        'is_admin': user.is_superuser,
                    }
                }
            })
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class LogoutView(APIView):

    @staticmethod
    def delete(request, format=None):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserGetSerializer


class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer
    queryset = User.objects.all()


class UserUpdateView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = (Or(IsAdminUser, IsAuthenticated),)
    @staticmethod
    def patch(request):
        try:
            serializer = UserSerializer(data=request.data)
            user = request.user
            username = request.data.get('username')
            user_image = request.data.get('user_image')
            if user_image:
                if username == user.username or not username:
                    user.profile.user_image = user_image
                    user.profile.save()
                    return Response("Изображение успешно обновлены")
                else:
                    user.profile.user_image = user_image
                    user.username = username
                    user.save()
                    user.profile.save()
                    return Response("Имя пользователя и изображение успешно обновлены")
            elif username != '':
                user.username = username
                user.save()
                return Response({
                    'status': 'succes',
                    'code': status.HTTP_200_OK,
                    'message': "Изменение успешно",
                    'data': {
                        'username': username,

                    },
                })
            else:
                return Response("Требуется изменение")
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class UserDeleteView(generics.GenericAPIView):
    permission_classes = (Or(IsAdminUser, IsAuthenticated), )
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.request.user
            user = request.user
            password = request.data.get('password')

            if not self.object.check_password(password):
                return Response({
                    'status': 'failed',
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': "Неправильный пароль",
                })
            user.delete()
            return Response({
                'status': 'succes',
                'code': status.HTTP_200_OK,
                'message': "Аккаунт успешно удален",
            }
            )
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


    def get_object(self):
        try:
            instance = self.queryset.get(username=self.request.user.username)
            return instance
        except User.DoesNotExist:
            raise Http404


class UserQuestionsView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = (Or(IsAdminUser, IsAuthenticated),)

    def get_queryset(self):
        try:
            questions = Answer.objects.filter(user=self.kwargs['user_id'])
            return questions
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class UserAnswersView(generics.ListAPIView):
    serializer_class = AnswerSerializer

    def get_queryset(self):
        try:
            answers = Answer.objects.filter(user=self.kwargs['user_id'])
            return answers
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class SubjectQuestionView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    
    def get_queryset(self):
        try:
            subject_questions = Question.objects.all()
            slug = self.kwargs['slug']
            subject_id = Subject.objects.get(slug=slug).id

            if subject_id is not None:
                subject_questions = Question.objects.filter(subject=subject_id)

            return subject_questions
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class QuestionListView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    # Qidiruv bo'yicha sozlamalar
    search_fields = ['text']
    filter_backends = (filters.SearchFilter,)

    def get_queryset(self):
        queryset = Question.objects.order_by('-id')
        return queryset


class QuestionDetailView(generics.RetrieveAPIView):
    serializer_class = QuestionSerializer
    queryset = Question.objects.all()


class QuestionUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = QuestionSerializer

    @staticmethod
    def post(request, pk):
        try:
            serializer = QuestionSerializer(data=request.data)
            question = Question.objects.get(id=pk)
            text = request.data.get('text')
            point = request.data.get('point')
            if serializer.is_valid():
                question.text = text
                question.point = point
                question.save()
                return Response({
                    'status': 'succes',
                    'code': status.HTTP_200_OK,
                    'message': "Успешно изменено",
                    'data': {
                        'id': question.id,
                        'question_text': question.text,
                        'question_point': question.point,

                    }
                })
            else:
                return Response("Введите всю данные", status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class QuestionDeleteView(generics.DestroyAPIView):
    serializer_class = QuestionSerializer
    permission_classes = (Or(IsAdminUser, IsAuthenticated), )

    def delete(self, request, pk):
        try:
            question = Question.objects.get(id=pk)
            if question:
                question.delete()
                return Response({
                    'status': 'succes',
                    'code': status.HTTP_200_OK,
                    'message': "Успешно удалено",
                })
            else:
                return Response("Вопрос не найден", status=status.HTTP_404_NOT_FOUND)
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class AnswerListView(generics.ListAPIView):
    serializer_class = AnswerSerializer
    permission_classes = (Or(IsAdminUser, IsAuthenticated),)

    def get_queryset(self):
        queryset = Answer.objects.all()
        return queryset


class AnswerDetailView(generics.RetrieveAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer


class AnswerUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = AnswerSerializer

    @staticmethod
    def post(request, pk):
        try:
            serializer = AnswerSerializer(data=request.data)
            answer = Answer.objects.get(id=pk)
            text = request.data.get('text')
            if serializer.is_valid():
                answer.text = text
                answer.save()
                return Response({
                    'status': 200,
                    'message': 'Успешно изменено',
                    'data': {
                        'id': answer.id,
                        'answer_text': answer.text,
                    }
                })
            else:
                return Response("Введите всю данные", status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class AnswerDeleteView(generics.DestroyAPIView):
    serializer_class = AnswerSerializer
    permission_classes = (Or(IsAdminUser, IsAuthenticated),)

    def delete(self, request, pk):
        try:
            answer = Answer.objects.get(id=pk)
            if answer:
                answer.delete()
                return Response({
                    'status': 200,
                    'message': 'Успешно удалено',
                })
            else:
                return Response("Не найден", status=status.HTTP_404_NOT_FOUND)
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class RatingListView(generics.ListAPIView):
    serializer_class = RatingSerializer

    def get_queryset(self):
        queryset = RatingCalc.objects.all()
        return queryset


class UsersByRatingView(generics.ListAPIView):
    serializer_class = UserGetSerializer

    def get_queryset(self):
        queryset = User.objects.order_by('-profile__rating')
        return queryset


class CommmentListView(generics.ListAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        queryset = Comment.objects.all()
        return queryset


class ChangePasswordView(generics.UpdateAPIView):

    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            user = request.user
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                # Eski parolni tekshirish
                if not self.object.check_password(serializer.data.get("old_password")):
                    return Response("Неверный пароль", status=status.HTTP_400_BAD_REQUEST)
                else:
                    # parolni yangilash
                    self.object.set_password(serializer.data.get("new_password"))
                    self.object.save()
                    response = {
                        'status': 'success',
                        'code': status.HTTP_200_OK,
                        'message': 'Пароль обновлен',
                        'data': {
                            'username': user.username,
                        }
                    }

                    return Response(response)

            else:
                return Response("Введите всю данные", status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class CommmentCreateView(generics.GenericAPIView):
    serializer_class = CommentSerializer

    @staticmethod
    def post(request):
        try:
            serializer = CommentSerializer(data=request.data)
            answer_id = request.data.get('answer')
            text = request.data.get('text')
            user_id = request.user.pk
            if serializer.is_valid():
                serializer.save(user_id=user_id, answer_id=answer_id, text=text)
                return Response({
                    'status': 200,
                    'message': 'Успешно создано',
                    'data': {
                        'user_id': user_id,
                        'answer_id': answer_id,
                        'commment': text,
                    },
                })
            else:
                return Response("Введите всю данные", status=status.HTTP_400_BAD_REQUEST)

        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class BestCreateView(generics.GenericAPIView):
    serializer_class = AnswerSerializer

    @staticmethod
    def post(request):
        try:
            serializer = AnswerSerializer(data=request.data)
            answer_id = request.data.get('answer_id')
            answer = Answer.objects.get(id=answer_id)
            user_id = answer.user_id
            user = User.objects.get(id=user_id)
            best_answers = Profile.objects.get(user_id=user_id).best_answers
            is_best = request.data.get('is_best')
            if serializer.is_valid():
                if is_best:
                    answer.is_best = is_best
                    answer.save()
                    best_answers += 1
                    user.profile.best_answers = best_answers
                    user.profile.save()
                    return Response({
                        'status': 200,
                        'data': 'Best is True'
                    })
                return Response('False')
            else:
                return Response("Введите всю данные", status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class HelpListView(generics.ListAPIView):
    serializer_class = HelpSerializer

    def get_queryset(self):
        queryset = Help.objects.all()
        return queryset


class HelpCreateView(generics.GenericAPIView):
    serializer_class = HelpSerializer

    @staticmethod
    def post(request):
        try:
            serializer = HelpSerializer(data=request.data)
            question_id = request.data.get('question')
            text = request.data.get('text')
            user_id = request.user.pk
            if serializer.is_valid():
                if Help.objects.filter(user_id=user_id, question_id=question_id, text=text).first():
                    return Response({

                        'status': 'failed',
                        'code': status.HTTP_400_BAD_REQUEST,
                        'message': "Сообщение уже есть",
                    })
                else:
                    serializer.save(user_id=user_id,
                                    question_id=question_id, text=text)
                    return Response({

                        'status': 'succes',
                        'code': status.HTTP_200_OK,
                        'message': "Успешно создано",
                        'data': {
                            'user_id': user_id,
                            'question_id': question_id,
                            'text': text,
                        },
                    })

            else:
                return Response("Введите всю данные", status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class QuestionCreateView(generics.CreateAPIView):
    serializer_class = QuestionSerializer

    def post(self, request):
        try:
            serializer = QuestionSerializer(data=request.data)
            subject = request.data.get('subject')
            text = request.data.get('text')
            length = request.data.get('length')
            user_id = request.user.pk
            ball = -int(request.data.get('point'))
            ball_type = 'question'
            user = RatingCalc.objects.filter(user=user_id).exists()
            if not subject.isnumeric():
                return Response("Выберите один из предметов")
            else:
                if user:
                    last_sum = RatingCalc.objects.filter(
                        user_id=user_id).last().check_sum
                    m = hashlib.md5(
                        str(last_sum+str(user_id)+str(ball)+ball_type).encode('utf-8'))
                    check_sum = m.hexdigest()
                    print(last_sum)
                    print(check_sum)

                else:
                    m = hashlib.md5(
                        str(str(user_id)+str(ball)+ball_type).encode('utf-8'))
                    check_sum = m.hexdigest()
                    print(check_sum)
                sub_check = Subject.objects.filter(id=subject).exists()
                if sub_check is None or sub_check is False:
                    return Response({
                        'status': 'failed',
                        'code': status.HTTP_404_NOT_FOUND,

                    })
                if serializer.is_valid():
                    user = Profile.objects.get(user=user_id)
                    profile_ball = Profile.objects.get(user=user_id).rating
                    if (-ball) <= profile_ball:

                        profile_ball += int(ball)
                        user.rating = profile_ball
                        user.save()
                        question = serializer.save(subject_id=subject, user_id=user_id)
                        create_calc(user_id, check_sum, ball, ball_type)
                        for file_num in range(0, int(length)):
                            images = request.FILES.get(f'images{file_num}')
                            QuestionImage.objects.create(
                                question=question,
                                image=images
                            )
                            print(images,request.data)

                        return Response({
                            'status': 'succes',
                            'code': status.HTTP_200_OK,
                            'message': 'Успешно создано',
                            'data': {
                                'username': request.user.username,
                                'subject': subject,
                                'question': text,
                                'point': -ball,
                            }
                        },)
                    return Response(f'Ваша оценка за вопрос больше {profile_ball} ')

                else:
                    return Response("Введите всю данные", status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class AnswerCreateView(generics.CreateAPIView):
    serializer_class = AnswerSerializer

    def post(self, request):
        try:
            serializer = AnswerSerializer(data=request.data)
            question = request.data.get('question')
            text = request.data.get('text')
            length = request.data.get('length')
            user_id = request.user.pk
            ball = Question.objects.get(id=question).point
            subject = Question.objects.get(id=question).subject_id
            ball_type = 'answer'
            user = RatingCalc.objects.filter(user=user_id).exists()
            answers = Answer.objects.filter(question_id=question).count()
            if answers >= 2:
                return Response({

                    'status': "failed",
                    'code': 400,
                    'message': 'На этот вопрос нельзя ответить',

                },
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                if user:
                    last_sum = RatingCalc.objects.filter(
                        user_id=user_id).last().check_sum
                    m = hashlib.md5(str(last_sum + str(user_id) +
                                        str(ball) + ball_type).encode('utf-8'))
                    check_sum = m.hexdigest()


                else:
                    m = hashlib.md5(
                        str(str(user_id) + str(ball) + ball_type).encode('utf-8'))
                    check_sum = m.hexdigest()
                    print(check_sum)

                if serializer.is_valid():
                    user = Profile.objects.get(user=user_id)
                    profile_ball = Profile.objects.get(user=user_id).rating
                    print(profile_ball)
                    profile_ball += int(ball)
                    user.rating = profile_ball
                    print(user.rating)
                    user.save()

                    answer = serializer.save(question_id=question,
                                             user_id=user_id, subject_id=subject)
                    create_calc(user_id, check_sum, ball, ball_type)
                    if length:
                        for file_num in range(0, int(length)):
                                images = request.data.get(f'images{file_num}')
                                AnswerImage.objects.create(
                                    answer=answer,
                                    images=images
                                )
                                print(images,request.data)
                    else:
                        print("Rasmsiz")
                    return Response({

                        'status': "succes",
                        'code': 200,
                        'message': 'Успешно создано',
                        'data': {
                            'user': user.pk,
                            'question_id': question,
                            'answer': text,
                        }
                    },
                        status=status.HTTP_201_CREATED)
                else:
                    return Response("Введите всю данные", status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)


class ThanksView(generics.CreateAPIView):
    serializer_class = AnswerSerializer

    def post(self, request):
        try:
            answer_id = request.data.get('id')
            answer = Answer.objects.get(id=answer_id)
            user_id = request.user.pk
            thank_check = Thank.objects.filter(user_id=user_id, answer_id=answer_id)
            if thank_check:
                return Response("Только один раз", status=status.HTTP_208_ALREADY_REPORTED)
            else:

                thank = Thank.objects.create(
                    answer_id=answer_id, count=1, user_id=user_id)
                thank.save()
                user = User.objects.get(id=answer.user_id)
                user.profile.thanks += 1
                user.profile.save()

                return Response({
                    'status': 200,
                    'message': 'Успешно создано',
                    'data': {
                        'answer': answer.text,
                    },
                })

        except:
            return Response("Произошла ошибка", status=status.HTTP_400_BAD_REQUEST)

