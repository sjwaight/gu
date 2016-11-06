from django.db import models
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db.models import Max
from decimal import *

from filebrowser.fields import FileBrowseField

from . import settings
from . import utils
from socialmedia.common import SCHEDULE_RESULTS

import logging
import datetime
import sys

logger = logging.getLogger("django")


class Author(models.Model):
    first_names = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200)
    title = models.CharField(max_length=20, blank=True)
    photo = FileBrowseField(max_length=200, directory="images/",
                            blank=True, null=True, )
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=200, blank=True)
    facebook = models.CharField(max_length=200, blank=True)
    googleplus = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    email_is_private = models.BooleanField(default=True)
    freelancer = models.BooleanField(default=False)
    telephone = models.CharField(max_length=200, blank=True)
    cell = models.CharField(max_length=200, blank=True)

    ### Fields that contain default values for invoices
    identification = models.CharField(max_length=20, blank=True, help_text=
                                      "SA ID, passport or some form "
                                      "of official identification")
    dob = models.DateField(blank=True, null=True, verbose_name="date of birth",
                           help_text="Please fill this in. Required by SARS.")
    address = models.TextField(blank=True,
                               help_text="Please fill this in. Required by SARS.")
    bank_name = models.CharField(max_length=20, blank=True)
    bank_account_number = models.CharField(max_length=20, blank=True)
    bank_account_type = models.CharField(max_length=20, default="CURRENT")
    bank_branch_name = models.CharField(max_length=20, blank=True,
                                        help_text="Unnecessary for Capitec, "
                                        "FNB, Standard, Nedbank and Absa")
    bank_branch_code = models.CharField(max_length=20, blank=True,
                                        help_text="Unnecessary for Capitec, "
                                        "FNB, Standard, Nedbank and Absa")
    swift_code = models.CharField(max_length=12, blank=True,
                                  help_text="Only relevant for banks outside SA")
    iban = models.CharField(max_length=34, blank=True,
                             help_text="Only relevant for banks outside SA")
    tax_no = models.CharField(max_length=50, blank=True,
                              help_text="Necessary for SARS.")
    tax_percent = models.DecimalField(max_digits=2, decimal_places=0, default=25,
                                      verbose_name="tax %",
                                      help_text="Unless you have a tax directive"
                                      " we have to deduct 25% PAYE for SARS.")
    vat = models.DecimalField(max_digits=2, decimal_places=0, default=0,
                              verbose_name="vat %",
                              help_text="If you are VAT regisered "
                              "set this to 14 else leave at 0")

    ####
    user = models.OneToOneField(User, null=True, blank=True)
    password_changed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "first_names__icontains",
                "last_name__icontains",)

    def __str__(self):
        return " ".join([self.title, self.first_names,
                         self.last_name]).strip()

    def get_absolute_url(self):
        return reverse('author.detail', args=[self.pk, ])

    def save(self, *args, **kwargs):
        if self.pk is None:
            pwd = None
            site = Site.objects.get_current()
            if self.user is None:
                pwd = utils.generate_pwd()
                username = (self.first_names + self.last_name).replace(" ", "_")
                user = User.objects.create_user(username=username,
                                                first_name = self.first_names,
                                                last_name = self.last_name,
                                                email=self.email,
                                                password=pwd)
                user.save()
                self.user = user
                super(Author, self).save(*args, **kwargs)
            subject = "Account created for you on GroundUp"
            message = render_to_string('account/email/account_created_message.txt',
                                       {'user': user,
                                        'author': self,
                                        'pwd': pwd,
                                        'site': site})
            try:
                send_mail(subject,
                          message,
                          settings.EDITOR,
                          [self.email, settings.EDITOR,]
                )
            except:
                log_message = "Error author creation email failed: " + \
                              self.email
                logger.error(log_message)
        else:
            # Design error for legacy reasons: email is duplicated in Author
            # And User
            if self.user is not None:
                self.user.email = self.email
                self.user.save()
            super(Author, self).save(*args, **kwargs)

    class Meta:
        unique_together = (('first_names', 'last_name'), )
        ordering = ["last_name", "first_names", ]


class Region(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)

    def get_descendants(self):
        regions = Region.objects.filter(name__startswith=(self.name + "/"))
        return regions

    def get_absolute_url(self):
        return reverse('region.detail', args=[self.name, ])

    def __str__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "name__icontains",)

    class Meta:
        ordering = ['name', ]


class Topic(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    introduction = models.TextField(blank=True,
                                    help_text="Use unfiltered HTML. "
                                    "If this is not blank, "
                                    "the default template does not render any "
                                    "other fields before the article list.")
    icon = FileBrowseField("Image", max_length=200, directory="images/",
                           blank=True, null=True)
    template = models.CharField(max_length=200,
                                default="newsroom/topic_detail.html")

    def count_articles(self):
        return Article.objects.filter(topics=self).count()

    def get_absolute_url(self):
        return reverse('topic.detail', args=[self.slug, ])

    def __str__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "name__icontains",)

    class Meta:
        ordering = ['name', ]


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)

    def get_absolute_url(self):
        return reverse('category.detail', args=[self.slug, ])

    def __str__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains",)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ['name', ]


# Used to prevent disaster on the template fields
DETAIL_TEMPLATE_CHOICES = (
    ("newsroom/article_detail.html", "Standard"),
)

SUMMARY_TEMPLATE_CHOICES = (
    ("newsroom/article_summary.html", "Standard"),
    ("newsroom/photo_summary.html", "Great Photo"),
    ("newsroom/text_summary.html", "Text only"),
)

OVERRIDE_COMMISSION_CHOICES = (
    ("NO", "No"),
    ("PROCESS", "Process commissions for this article"),
    ("NOPROCESS", "Don't process commissions for this article"),
)

INVOICE_STATUS_CHOICES = (
    ("0", "Unpaid"),
    ("1", "Queried by reporter-unpaid"),
    ("2", "Approved by reporter-unpaid"),
    ("3", "Approved by editor-unpaid"),
    ("4", "Paid"),
)

class ArticleQuerySet(models.QuerySet):

    def published(self):
        return self.filter(published__lte=timezone.now())

    def list_view(self):
        return self.published().filter(exclude_from_list_views=False)


# def latest_article(request):
#    return Entry.objects.published().latest("modified").modified

class Article(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    summary_image = FileBrowseField("Image", max_length=200,
                                    directory="images/",
                                    blank=True, null=True)
    summary_image_size = models.CharField(
        default=settings.ARTICLE_SUMMARY_IMAGE_SIZE,
        max_length=20,
        help_text="Choose 'LEAVE' if image size should not be changed.")
    summary_image_alt = models.CharField(
        max_length=200,
        blank=True,
        help_text="Description of image for assistive technology.")
    summary_text = models.TextField(blank=True)
    author_01 = models.ForeignKey(Author, blank=True, null=True,
                                  related_name="author_01",
                                  verbose_name="first author")
    author_02 = models.ForeignKey(Author, blank=True, null=True,
                                  related_name="author_02",
                                  verbose_name="second author")
    author_03 = models.ForeignKey(Author, blank=True, null=True,
                                  related_name="author_03",
                                  verbose_name="third author")
    author_04 = models.ForeignKey(Author, blank=True, null=True,
                                  related_name="author_04",
                                  verbose_name="fourth author")
    author_05 = models.ForeignKey(Author, blank=True, null=True,
                                  related_name="author_05",
                                  verbose_name="fifth author")
    byline = models.CharField(max_length=200, blank=True,
                              verbose_name='customised byline',
                              help_text="If this is not blank it "
                              "overrides the value of the author fields")
    primary_image = FileBrowseField(max_length=200, directory="images/",
                                    blank=True, null=True)
    primary_image_size = models.CharField(
        default=settings.ARTICLE_PRIMARY_IMAGE_SIZE,
        max_length=20,
        help_text="Choose 'LEAVE' if image size should not be changed.")
    primary_image_alt = models.CharField(
        max_length=200,
        blank=True,
        help_text="Description of image for assistive technology.")
    external_primary_image = models.URLField(blank=True, max_length=500,
                                             help_text="If the primary "
                                             "image has a value, "
                                             "it overrides this.")
    primary_image_caption = models.CharField(max_length=600, blank=True)
    body = models.TextField(blank=True)
    use_editor = models.BooleanField(default=True)
    published = models.DateTimeField(blank=True, null=True,
                                     verbose_name='publish time')
    recommended = models.BooleanField(default=True)
    category = models.ForeignKey(Category, default=4)
    region = models.ForeignKey(Region, blank=True, null=True)
    topics = models.ManyToManyField(Topic, blank=True)
    main_topic = models.ForeignKey(Topic, blank=True,
                                   null=True,
                                   related_name="main",
                                   help_text="Used for generating"
                                   "'See also' list of articles.")
    copyright = models.TextField(blank=True,
                                 default=settings.ARTICLE_COPYRIGHT)
    template = models.CharField(max_length=200,
                                choices=DETAIL_TEMPLATE_CHOICES,
                                default="newsroom/article_detail.html")
    summary_template = models.CharField(max_length=200,
                                        choices=SUMMARY_TEMPLATE_CHOICES,
                                        default="newsroom/article_summary.html")
    include_in_rss = models.BooleanField(default=True)
    letters_on = models.BooleanField(default=True)
    comments_on = models.BooleanField(default=False)
    collapse_comments = models.BooleanField(default=True)
    exclude_from_list_views = models.BooleanField(default=False)
    suppress_ads = models.BooleanField(default=False,
                                       help_text="Only suppresses ads "
                                       "that are external to article. "
                                       "You can still create ads in article.")
    promote_article = models.BooleanField(default=True)
    encourage_republish = models.BooleanField(default=True)
    activate_slideshow = models.BooleanField(default=False)
    additional_head_scripts = models.TextField(blank=True)
    additional_body_scripts = \
        models.TextField(blank=True,
                         help_text="Include things like additional javascript "
                         "that should come at bottom of article")
    undistracted_layout = models.BooleanField(default=False)
    # Neccessary for importing old Drupal articles
    disqus_id = models.CharField(blank=True, max_length=20)

    stickiness = models.IntegerField(
        default=0,
        help_text="The higher the value, the stickier the article.")
    slug = models.SlugField(max_length=200, unique=True)

    # Facebook
    facebook_wait_time = models.PositiveIntegerField(
        default=0,
        help_text="Minimum number of minutes "
        "after publication "
        "till post.")
    facebook_image = FileBrowseField(max_length=200, directory="images/",
                                     blank=True, null=True,
                                     verbose_name="image",
                                     help_text="Leave blank to use primary image.")
    facebook_image_caption = models.CharField(max_length=200,
                                              verbose_name="caption",
                                              help_text="Leave blank to use primary "
                                              "image caption.",
                                              blank=True)
    facebook_description = models.CharField(max_length=200,
                                            blank=True, help_text="Leave blank to use same text as summary.")
    facebook_message = models.TextField(blank=True,
                                        verbose_name="message",
                                        help_text="Longer status update that appears "
                                        "above the image in Facebook. ")
    facebook_send_status = models.CharField(max_length=20,
                                            choices=SCHEDULE_RESULTS,
                                            verbose_name="sent status",
                                            default="paused")
    last_tweeted = models.DateTimeField(default=
                                        datetime.datetime(year=2000,
                                                          month=1,day=1))
    # Logging
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    user = models.ForeignKey(User, default=1)
    version = models.PositiveIntegerField(default=0)

    # Author notifications and payments
    # notified_authors = models.BooleanField(default=False)
    author_payment = models.DecimalField(default=0.00, max_digits=9,
                                         decimal_places=2)
    override_commissions_system = models.CharField(choices=
                                                   OVERRIDE_COMMISSION_CHOICES,
                                                   default="NO", max_length=20)
    commissions_processed = models.BooleanField(default=False)

    # Cached fields
    cached_byline = models.CharField(max_length=500, blank=True)
    cached_byline_no_links = models.CharField(max_length=400, blank=True,
                                              verbose_name="Byline")
    cached_primary_image = models.URLField(blank=True, max_length=500)
    cached_summary_image = models.URLField(blank=True, max_length=500)
    cached_summary_text = models.TextField(blank=True)
    cached_summary_text_no_html = models.TextField(blank=True)

    cached_small_image = models.URLField(blank=True, max_length=500)

    objects = ArticleQuerySet.as_manager()

    def is_published(self):
        return (self.published is not None) and \
            (self.published <= timezone.now())

    def publish_now(self):
        if self.is_published() is False:
            self.published = timezone.now()
            self.save()

    is_published.boolean = True
    is_published.short_description = 'published'

    def unsticky(self):
        self.stickiness = 0
        self.save()

    def make_top_story(self):
        articles = Article.objects.filter(stickiness__gt=0)
        for article in articles:
            article.stickiness = 0
            article.save()
        self.stickiness = 1
        self.save()

    # Methods that calculate cache fields

    '''Used to generate the cached byline upon model save, so
    there's less processing for website user requests.
    '''

    def calc_byline(self, links=False):
        if self.byline:
            return self.byline
        else:
            names = [self.author_01, self.author_02,
                     self.author_03, self.author_04,
                     self.author_05
                     ]
            if links:
                names = ["<a rel=\"author\" href='" + name.get_absolute_url() +
                         "'>" + str(name) + "</a>"
                         for name in names if name != None]
            else:
                names = [str(name) for name in names if name != None]
        if len(names) == 0:
            return ""
        elif len(names) == 1:
            return "By " + names[0]
        elif len(names) == 2:
            return "By " + names[0] + " and " + names[1]
        else:
            names[-1] = " and " + names[-1]
            names_middle = [", " + name for name in names[1:-1]]
            names_string = names[0] + "".join(names_middle) + names[-1]
            return "By " + names_string

    '''Used to generate the cached primary image upon model save, so
    there's less processing for website user requests.
    '''

    def calc_primary_image(self):
        if self.primary_image:
            if self.primary_image_size == "LEAVE":
                return self.primary_image.url
            else:
                return self.primary_image.version_generate(
                    self.primary_image_size).url
        return self.external_primary_image

    '''Used to generate the cached summary image upon model save, so
    there's less processing for website user requests.
    '''

    def calc_summary_image(self):
        image_size = self.summary_image_size
        if self.summary_image:
            if self.summary_image_size == 'LEAVE':
                return self.summary_image.url
            else:
                return self.summary_image.version_generate(image_size).url

        if self.summary_image_alt == "":
            self.summary_image_alt = self.primary_image_alt

        if self.primary_image:
            if self.summary_image_size == 'LEAVE':
                return self.primary_image.url
            else:
                return self.primary_image.version_generate(image_size).url

        if self.external_primary_image:
            return self.external_primary_image

        return ""

    '''Used to generate the cached small image upon model save, so
    there's less processing for website user requests.
    '''

    def calc_small_image(self):
        if self.summary_image:
            return self.summary_image.version_generate("small").url

        if self.primary_image:
            return self.primary_image.version_generate("small").url

        if self.external_primary_image:
            return self.external_primary_image

        return ""

    '''Used to generate the cached summary text upon model save, so
    there's less processing for website user requests.
    '''

    def calc_summary_text(self):
        if self.summary_text:
            return self.summary_text
        if self.subtitle:
            return self.subtitle

        # Not very robust, but using BeautifulSoup was too slow
        # and the server would time out.
        start_para = str(self.body).partition("<p")

        if start_para[2] == None:
            return ""
        start_para = start_para[2].partition(">")

        if start_para[2] == None:
            return ""
        end_para = start_para[2].partition("</p>")

        if end_para[1] == None or end_para[0] == None:
            return ""
        return strip_tags(end_para[0])

    '''Legacy code from when more complex processing was done. But too
    time-consuming and server times out.
    '''

    def calc_summary_text_no_html(self):
        return strip_tags(self.cached_summary_text)

    def save(self, *args, **kwargs):
        self.cached_byline = self.calc_byline(True)
        self.cached_byline_no_links = self.calc_byline(False)

        try:
            self.cached_primary_image = self.calc_primary_image()
        except:
            self.cached_primary_image = ""
        try:
            self.cached_summary_text = self.calc_summary_text()
        except:
            self.cached_summary_text = ""
        try:
            self.cached_summary_text_no_html = self.calc_summary_text_no_html()
        except:
            self.cached_summary_text_no_html = ""
        try:
            self.cached_summary_image = self.calc_summary_image()
        except:
            self.cached_summary_image = ""
        try:
            self.cached_small_image = self.calc_small_image()
        except:
            self.cached_small_image = ""
        self.version = self.version + 1
        super(Article, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('article.detail', args=[self.slug, ])

    def __str__(self):
        return str(self.pk) + " " + self.title

    class Meta:
        ordering = ["-stickiness", "-published", ]


class UserEdit(models.Model):
    article = models.ForeignKey(Article)
    user = models.ForeignKey(User)
    edit_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('article', 'user',)
        ordering = ['article__published', 'edit_time', ]

    def __str__(self):
        return ", ".join([str(self.article), str(self.user),
                          str(self.edit_time)])


class MostPopular(models.Model):
    '''This table's records each contain a list of the
    most popular articles as returned by the management command
    mostpopular.
    The latest (or only) record in this table can be obtained
    by views that display the most popular articles.
    The most popular articles are stored as a comma-delimited list
    in the article_list field.
    '''
    article_list = models.TextField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.article_list[0:100]

    @staticmethod
    def get_most_popular_list():
        try:
            mostpopular = MostPopular.objects.latest("modified")
            article_list = mostpopular.article_list.split("\n")
            article_list = [item.split("|") for item in article_list]
        except MostPopular.DoesNotExist:
            article_list = None
        return article_list

    @staticmethod
    def get_most_popular_html():
        article_list = MostPopular.get_most_popular_list()
        if article_list:
            html = "<ol class='most-popular'>"
            for article in article_list:
                entry = "<li><a href='" + \
                        reverse('article.detail', args=[article[0]]) + \
                        "'>" + article[1] + "</a></li>"
                html = html + entry
            html = html + "</ol>"
        else:
            html = ""
        return html

    class Meta:
        verbose_name_plural = "most popular"


class Fund(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name.upper()

    class Meta:
        ordering = ['name',]

EXTENSIONS = [".jpg", ".pdf", ".doc", ".docx", ".odt", ".xls", ".xlsx",
              ".zip", ".JPG", ".PDF", ".DOC", ".DOCX"]

class Invoice(models.Model):
    author = models.ForeignKey(Author)
    invoice_num = models.IntegerField(default=0)
    # Fields whose default values are taken from Author
    identification = models.CharField(max_length=20, blank=True, help_text=
                                      "SA ID, passport or some form "
                                      "of official identification")
    dob = models.DateField(blank=True, null=True, verbose_name="date of birth",
                           help_text="Please fill this in. Required by SARS.")
    address = models.TextField(blank=True,
                               help_text="Please fill this in. Required by SARS.")
    bank_name = models.CharField(max_length=20, blank=True)
    bank_account_number = models.CharField(max_length=20, blank=True)
    bank_account_type = models.CharField(max_length=20, default="CURRENT")
    bank_branch_name = models.CharField(max_length=20, blank=True,
                                        help_text="Unnecessary for Capitec, "
                                        "FNB, Standard, Nedbank and Absa")
    bank_branch_code = models.CharField(max_length=20, blank=True,
                                        help_text="Unnecessary for Capitec, "
                                        "FNB, Standard, Nedbank and Absa")
    swift_code = models.CharField(max_length=12, blank=True,
                                  help_text="Only relevant for banks outside SA")
    iban = models.CharField(max_length=34, blank=True,
                             help_text="Only relevant for banks outside SA")
    tax_no = models.CharField(max_length=50, blank=True,
                              verbose_name="tax number",
                              help_text="Necessary for SARS.")
    tax_percent = models.DecimalField(max_digits=2, decimal_places=0, default=25,
                                      verbose_name="tax %",
                                      help_text="Unless you have a tax directive"
                                      " we have to deduct 25% PAYE for SARS.")
    vat = models.DecimalField(max_digits=2, decimal_places=0, default=0,
                              verbose_name="vat %",
                              help_text="If you are VAT regisered "
                              "set this to 14 else leave at 0")
    ####
    paid = models.BooleanField(default=False)
    amount_paid = models.DecimalField(max_digits=8,
                                      decimal_places=2, default=0.00,
                                      verbose_name="amount")
    tax_paid = models.DecimalField(max_digits=8,
                                      decimal_places=2, default=0.00)
    vat_paid = models.DecimalField(max_digits=8,
                                      decimal_places=2, default=0.00)
    invoice = FileBrowseField(max_length=200, directory="commissions/invoices/",
                              blank=True, null=True, extensions=EXTENSIONS)
    proof = FileBrowseField(max_length=200, directory="commissions/proofs/",
                            blank=True, null=True, extensions=EXTENSIONS)
    status = models.CharField(max_length=2, choices=INVOICE_STATUS_CHOICES,
                              default="0")
    notes = models.TextField(blank=True)
    date_time_reporter_approved = models.DateTimeField(null=True, blank=True,
                                                       editable=False)
    date_time_editor_approved = models.DateTimeField(null=True, blank=True,
                                                     editable=False)
    date_time_processed = models.DateTimeField(null=True, blank=True,
                                               editable=False)
    date_notified_payment = models.DateTimeField(null=True, blank=True,
                                               editable=False)
    our_reference = models.CharField(max_length=20, blank=True)
    their_reference = models.CharField(max_length=20, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def calc_payment(self):
        commissions = Commission.objects.filter(invoice=self).\
                      filter(fund__isnull=False).\
                      filter(commission_due__gt=0.00)
        total_uncorrected = Decimal(0.00)
        total_paid = Decimal(0.00)
        total_tax = Decimal(0.00)
        total_vat = Decimal(0.00)
        for commission in commissions:
            (due, vat, tax, uncorrected) = commission.calc_payment()
            total_paid = total_paid + due
            total_vat = total_vat + vat
            total_tax = total_tax + tax
        self.amount_paid = total_paid
        self.vat_paid = total_vat
        self.tax_paid = total_tax
        return (self.amount_paid, self.vat_paid,
                self.tax_paid, total_uncorrected,)

    def __str__(self):
        return str(self.pk) + "-" + str(self.invoice_num) + " - " + \
            str(self.author) + " - " + self.get_status_display()

    def short_string(self):
        return str(self.pk) + "-" + str(self.invoice_num)

    def save(self, *args, **kwargs):
        if self.status == "2": # Reporter has approved
            if self.date_time_reporter is None:
                self.date_time_reporter_approved = timezone.now()
        if self.status == "3": # Editor has approved
            if self.date_time_editor_approved is None:
                self.date_time_editor_approved = timezone.now()
        if self.status == "4": # Invoice has been paid
            if self.date_time_editor_approved is None:
                self.date_time_processed = timezone.now()
            self.calc_payment()
        super(Invoice, self).save(*args, **kwargs)


    @staticmethod
    def create_invoice(author):
        max_invoice = Invoice.objects.filter(author=author).\
                  aggregate(Max('invoice_num'))
        if max_invoice["invoice_num__max"] is None:
            invoice_num = 1
        else:
            invoice_num = max_invoice["invoice_num__max"] + 1
        invoice = Invoice()
        invoice.author = author
        invoice.invoice_num = invoice_num
        invoice.identification = author.identification
        invoice.dob = author.dob
        invoice.address = author.address
        invoice.bank_name = author.bank_name
        invoice.bank_account_number = author.bank_account_number
        invoice.bank_branch_name = author.bank_branch_name
        invoice.bank_branch_code = author.bank_branch_code
        invoice.swift_code = author.swift_code
        invoice.iban = author.iban
        invoice.tax_no = author.tax_no
        invoice.tax_percent = author.tax_percent
        invoice.vat = author.vat
        invoice.save()
        return invoice

    class Meta:
        ordering = ['-status','-modified',]



# Should have been named "Payment" hence the verbose_name
class Commission(models.Model):
    invoice = models.ForeignKey(Invoice, blank=True, null=True)
    # The author field is now deprecated and must be removed
    # once all legacy payments are processed
    author = models.ForeignKey(Author, blank=True, null=True)

    article = models.ForeignKey(Article, blank=True, null=True)
    description = models.CharField(max_length=30, blank=True,
                                   default="Article author")
    fund = models.ForeignKey(Fund, blank=True, null=True,
                             help_text="Selecting a fund approves the commission")
    sys_generated = models.BooleanField(default=False)
    date_generated = models.DateTimeField(blank=True, null=True)
    date_approved = models.DateField(blank=True, null=True)
    date_notified_approved = models.DateTimeField(blank=True, null=True)
    commission_due = models.DecimalField(max_digits=7,
                                         decimal_places=2, default=0.00,
                                         verbose_name="amount")
    taxable = models.BooleanField(default=True)
    vatable = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def save(self, *args, **kwargs):
        if self.fund is not None and self.date_approved is None:
            self.date_approved = timezone.now()
        super(Commission, self).save(*args, **kwargs)

    def calc_payment(self):
        vat = Decimal(0.00)
        if self.taxable:
            tax = (self.invoice.tax_percent / Decimal(100.00)) * \
                  self.commission_due
        else:
            tax = Decimal(0.00)
        if self.vatable:
                vat = (self.vat / Decimal(100.00))  * commission.commission_due
        else:
            vat = Decimal(0.00)
        due = self.commission_due - tax + vat
        return (due, vat, tax, self.commission_due)


    def __str__(self):
        return " ".join([str(self.pk), str(self.invoice.author),
                         str(self.article)])

    class Meta:
        ordering = ['author', 'article',]

# Signals

from allauth.account.signals import password_changed
from django.dispatch import receiver

@receiver(password_changed)
def set_password_reset(sender, **kwargs):
    author = kwargs["user"].author
    if author.password_changed == False:
        author.password_changed = True
        author.save()
