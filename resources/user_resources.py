#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import falcon
from falcon.media.validators import jsonschema
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import messages
from db.models import User, GenereEnum, Favour, UserToken
from hooks import requires_auth
from resources.base_resources import DAMCoreResource
from resources.schemas import SchemaRegisterUser, SchemaUpdateUser

mylogger = logging.getLogger(__name__)


@falcon.before(requires_auth)
class ResourceGetUserProfile(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetUserProfile, self).on_get(req, resp, *args, **kwargs)

        user_id = req.get_param("user_id", False)
        try:
            aux_user = self.db_session.query(User).filter(User.id == user_id).one()
            resp.media = aux_user.public_profile
            resp.status = falcon.HTTP_200
        except NoResultFound:
            raise falcon.HTTPBadRequest(description=messages.user_not_found)


class ResourceRegisterUser(DAMCoreResource):
    @jsonschema.validate(SchemaRegisterUser)
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceRegisterUser, self).on_post(req, resp, *args, **kwargs)

        aux_user = User()

        try:
            aux_user.username = req.media["username"]
            aux_user.password = req.media["password"]
            aux_user.email = req.media["email"]

            self.db_session.add(aux_user)

            try:
                self.db_session.commit()
            except IntegrityError:
                raise falcon.HTTPBadRequest(description=messages.user_exists)

        except KeyError:
            raise falcon.HTTPBadRequest(description=messages.parameters_invalid)

        resp.status = falcon.HTTP_200

class ResourceGetFavours(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetFavours, self).on_get(req, resp, *args, **kwargs)

        try:
            aux_user = self.db_session.query(Favour)
            resp.media = aux_user.getFavour
            resp.status = falcon.HTTP_200
        except NoResultFound:
            raise falcon.HTTPBadRequest(description=messages.user_not_found)


@falcon.before(requires_auth)
class ResourceLogOut(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceLogOut, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]
        try:
            todelete = self.db_session.query(UserToken).filter(UserToken.user_id == current_user.id).delete()
            self.db_session.commit()
            resp.status = falcon.HTTP_200
        except NoResultFound:
            raise falcon.HTTPBadRequest(description=messages.user_not_found)

@falcon.before(requires_auth)
class UpdateUser(DAMCoreResource):
    @jsonschema.validate(SchemaUpdateUser)
    def on_post(self, req, resp, *args, **kwargs):
        super(UpdateUser, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]
        #Assegurar que el id del favor correspon al id del usuari

        if "id" in kwargs:
            try:
                favour = self.db_session.query(User).filter(UserToken.user_id == current_user.id).one()
                if (req.media["username"]) is not None:
                    current_user.user = req.media["username"]
                if (req.media["email"]) is not None:
                    current_user.email = req.media["email"]
                if (req.media["phone"]) is not None:
                    current_user.phone = req.media["phone"]
                if (req.media["password"]) is not None:
                    current_user.password = req.media["password"]
                self.db_session.add(favour)
                self.db_session.commit()

                resp.status = falcon.HTTP_200

            except NoResultFound:
                raise falcon.HTTPBadRequest(description=messages.user_not_found) #TODO