#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_err_fun(double *nom_x, double *delta_x, double *out_6124982986690300985);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_7226860311726364703);
void car_H_mod_fun(double *state, double *out_5003902560509869510);
void car_f_fun(double *state, double dt, double *out_2108643631793349162);
void car_F_fun(double *state, double dt, double *out_976092077717257801);
void car_h_25(double *state, double *unused, double *out_7060178833911731904);
void car_H_25(double *state, double *unused, double *out_8539149688015017266);
void car_h_24(double *state, double *unused, double *out_1387198864840481973);
void car_H_24(double *state, double *unused, double *out_6354233611493861621);
void car_h_30(double *state, double *unused, double *out_8438839249442334751);
void car_H_30(double *state, double *unused, double *out_6020816729507768639);
void car_h_26(double *state, double *unused, double *out_5402053197998002066);
void car_H_26(double *state, double *unused, double *out_6166091066820478126);
void car_h_27(double *state, double *unused, double *out_4455773513103034253);
void car_H_27(double *state, double *unused, double *out_8195580041308193550);
void car_h_29(double *state, double *unused, double *out_7835523364765857234);
void car_H_29(double *state, double *unused, double *out_5510585385193376455);
void car_h_28(double *state, double *unused, double *out_5402807878801675955);
void car_H_28(double *state, double *unused, double *out_7853759671446644587);
void car_h_31(double *state, double *unused, double *out_821093816842317281);
void car_H_31(double *state, double *unused, double *out_5539882964587126650);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}