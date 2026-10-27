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
void car_err_fun(double *nom_x, double *delta_x, double *out_9074734778873374225);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8103998558374365190);
void car_H_mod_fun(double *state, double *out_387978277478947035);
void car_f_fun(double *state, double dt, double *out_4763203206369738804);
void car_F_fun(double *state, double dt, double *out_1016500512322045568);
void car_h_25(double *state, double *unused, double *out_1860729718252120477);
void car_H_25(double *state, double *unused, double *out_9152136137538215632);
void car_h_24(double *state, double *unused, double *out_694198277336709874);
void car_H_24(double *state, double *unused, double *out_5736682337369012848);
void car_h_30(double *state, double *unused, double *out_2984511561861269912);
void car_H_30(double *state, double *unused, double *out_6776274977664087357);
void car_h_26(double *state, double *unused, double *out_6665923047582284564);
void car_H_26(double *state, double *unused, double *out_5990081966410535383);
void car_h_27(double *state, double *unused, double *out_1555543571396949539);
void car_H_27(double *state, double *unused, double *out_8951038289464512268);
void car_h_29(double *state, double *unused, double *out_8326378797747300475);
void car_H_29(double *state, double *unused, double *out_6266043633349695173);
void car_h_28(double *state, double *unused, double *out_3446129696263896106);
void car_H_28(double *state, double *unused, double *out_7098301423290325869);
void car_h_31(double *state, double *unused, double *out_6020542932501928708);
void car_H_31(double *state, double *unused, double *out_6616290068643886859);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}